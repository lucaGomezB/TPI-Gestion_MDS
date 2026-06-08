"""Repository for atrasados, ranking, and reportes queries.

Provides read-only query methods that join Calificacion with EntradaPadron
and VersionPadron. No mutations — all endpoints in this module are GET only.

Design (per C-09 design.md):
- D1: Separate repository from CalificacionesRepository to keep JOIN-heavy
      queries isolated from grade CRUD.
- D2: Repository returns raw data; the service layer applies RN-06 logic
      to determine which students are atrasados.
- D3: Ranking uses COUNT + HAVING in SQL; HAVING excludes 0-approved students.
- D4: Scope filter (cargado_por) applied as optional repository parameter.
"""

from datetime import date
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.calificaciones import Calificacion
from app.models.padron import EntradaPadron, VersionPadron


class AtrasadosRankingRepository:
    """Tenant-scoped repository for atrasados/ranking/reportes queries.

    Args:
        session: An active SQLAlchemy ``AsyncSession``.
        tenant_id: The tenant UUID string for data isolation.
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _get_active_version(self, materia_id: str) -> VersionPadron | None:
        """Find the active padron version for a materia.

        Args:
            materia_id: The materia UUID.

        Returns:
            The active ``VersionPadron``, or ``None``.
        """
        stmt = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.activa == True,  # noqa: E712
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Alumnos con calificaciones (for atrasados detection, D2) ────────────

    async def get_alumnos_con_calificaciones(
        self,
        materia_id: str,
        cargado_por: str | None = None,
        comision: str | None = None,
        busqueda: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        """Get all active padron students with their calificaciones.

        Returns one dict per student with their grade records. Students
        without any grades are included (LEFT JOIN behavior in service).

        Args:
            materia_id: The materia UUID.
            cargado_por: If set, only includes grades loaded by this user.
            comision: Optional filter by comision name.
            busqueda: Optional ILIKE search on nombre/apellidos.
            fecha_desde: Only consider grades imported on or after this date.
            fecha_hasta: Only consider grades imported on or before this date.

        Returns:
            A list of dicts with student data and calificaciones.
        """
        version = await self._get_active_version(materia_id)
        if version is None:
            return []

        stmt = (
            select(EntradaPadron)
            .where(
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.version_id == version.id,
            )
        )

        if comision:
            stmt = stmt.where(EntradaPadron.comision == comision)
        if busqueda:
            pattern = f"%{busqueda}%"
            stmt = stmt.where(
                EntradaPadron.nombre.ilike(pattern)
                | EntradaPadron.apellidos.ilike(pattern)
            )

        # Eager load calificaciones with optional filters
        cali_loader = joinedload(EntradaPadron.calificaciones)
        cali_loader = cali_loader.where(Calificacion.materia_id == materia_id)
        if cargado_por is not None:
            cali_loader = cali_loader.where(
                Calificacion.cargado_por == cargado_por
            )
        if fecha_desde is not None:
            cali_loader = cali_loader.where(
                Calificacion.importado_at >= fecha_desde
            )
        if fecha_hasta is not None:
            cali_loader = cali_loader.where(
                Calificacion.importado_at <= fecha_hasta
            )

        stmt = stmt.options(cali_loader)

        result = await self.session.execute(stmt)
        entries = list(result.scalars().all())

        # Build dict representation
        alumnos: list[dict] = []
        for entry in entries:
            calificaciones = [
                {
                    "nota_numerica": (
                        float(c.nota_numerica) if c.nota_numerica is not None else None
                    ),
                    "nota_textual": c.nota_textual,
                    "aprobado": c.aprobado,
                    "actividad": c.actividad,
                    "importado_at": c.importado_at,
                }
                for c in entry.calificaciones
            ]
            alumnos.append({
                "entrada_padron_id": entry.id,
                "nombre": entry.nombre,
                "apellidos": entry.apellidos,
                "email": entry.email,
                "comision": entry.comision,
                "calificaciones": calificaciones,
            })

        return alumnos

    # ── Ranking (D3: COUNT + HAVING in SQL) ────────────────────────────────

    async def get_ranking(
        self,
        materia_id: str,
        cargado_por: str | None = None,
        comision: str | None = None,
        busqueda: str | None = None,
    ) -> list[dict]:
        """Get ranking of students by approved activities (RN-09).

        Only students with at least one approved activity are included
        (HAVING > 0). Ordered by total_aprobadas descending.

        Args:
            materia_id: The materia UUID.
            cargado_por: If set, only considers grades loaded by this user.
            comision: Optional filter by comision name.
            busqueda: Optional ILIKE search on nombre/apellidos.

        Returns:
            A list of dicts with ranking data.
        """
        version = await self._get_active_version(materia_id)
        if version is None:
            return []

        # Subquery: aggregate calificaciones per student
        cali_subq = (
            select(
                Calificacion.entrada_padron_id,
                func.count().label("total_actividades"),
                func.count()
                .filter(Calificacion.aprobado == True)  # noqa: E712
                .label("total_aprobadas"),
            )
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
            )
            .group_by(Calificacion.entrada_padron_id)
            .having(
                func.count()
                .filter(Calificacion.aprobado == True)  # noqa: E712
                > 0
            )
            .subquery()
        )

        if cargado_por is not None:
            cali_subq = (
                select(
                    Calificacion.entrada_padron_id,
                    func.count().label("total_actividades"),
                    func.count()
                    .filter(Calificacion.aprobado == True)  # noqa: E712
                    .label("total_aprobadas"),
                )
                .where(
                    Calificacion.tenant_id == self.tenant_id,
                    Calificacion.materia_id == materia_id,
                    Calificacion.cargado_por == cargado_por,
                )
                .group_by(Calificacion.entrada_padron_id)
                .having(
                    func.count()
                    .filter(Calificacion.aprobado == True)  # noqa: E712
                    > 0
                )
                .subquery()
            )

        stmt = (
            select(
                EntradaPadron,
                cali_subq.c.total_actividades,
                cali_subq.c.total_aprobadas,
            )
            .join(
                cali_subq,
                EntradaPadron.id == cali_subq.c.entrada_padron_id,
            )
            .where(
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.version_id == version.id,
            )
            .order_by(cali_subq.c.total_aprobadas.desc())
        )

        if comision:
            stmt = stmt.where(EntradaPadron.comision == comision)
        if busqueda:
            pattern = f"%{busqueda}%"
            stmt = stmt.where(
                EntradaPadron.nombre.ilike(pattern)
                | EntradaPadron.apellidos.ilike(pattern)
            )

        result = await self.session.execute(stmt)
        rows = result.all()

        ranking: list[dict] = []
        for entry, total_actividades, total_aprobadas in rows:
            ranking.append({
                "entrada_padron_id": entry.id,
                "nombre": entry.nombre,
                "apellidos": entry.apellidos,
                "comision": entry.comision,
                "total_actividades": total_actividades,
                "total_aprobadas": total_aprobadas,
            })

        return ranking

    # ── Metrics (for reportes endpoint) ──────────────────────────────────

    async def get_metricas(
        self,
        materia_id: str,
        cargado_por: str | None = None,
    ) -> dict:
        """Get consolidated subject metrics.

        Args:
            materia_id: The materia UUID.
            cargado_por: If set, only considers grades loaded by this user.

        Returns:
            A dict with keys: total_alumnos, alumnos_con_calificaciones,
            total_aprobadas, total_calificaciones, actividades.
        """
        version = await self._get_active_version(materia_id)

        total_alumnos = 0
        if version is not None:
            stmt_count = (
                select(func.count())
                .select_from(EntradaPadron)
                .where(
                    EntradaPadron.tenant_id == self.tenant_id,
                    EntradaPadron.version_id == version.id,
                )
            )
            result = await self.session.execute(stmt_count)
            total_alumnos = result.scalar() or 0

        # Base calificaciones query
        cali_base = select(Calificacion).where(
            Calificacion.tenant_id == self.tenant_id,
            Calificacion.materia_id == materia_id,
        )
        if cargado_por is not None:
            cali_base = cali_base.where(
                Calificacion.cargado_por == cargado_por
            )

        # Alumnos con al menos una calificacion
        stmt_con_cali = (
            select(func.count(func.distinct(Calificacion.entrada_padron_id)))
            .select_from(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
            )
        )
        if cargado_por is not None:
            stmt_con_cali = stmt_con_cali.where(
                Calificacion.cargado_por == cargado_por
            )
        result = await self.session.execute(stmt_con_cali)
        alumnos_con_calificaciones = result.scalar() or 0

        # Total aprobadas
        stmt_aprobadas = (
            select(func.count())
            .select_from(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.aprobado == True,  # noqa: E712
            )
        )
        if cargado_por is not None:
            stmt_aprobadas = stmt_aprobadas.where(
                Calificacion.cargado_por == cargado_por
            )
        result = await self.session.execute(stmt_aprobadas)
        total_aprobadas = result.scalar() or 0

        # Total calificaciones
        stmt_total_cali = (
            select(func.count())
            .select_from(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
            )
        )
        if cargado_por is not None:
            stmt_total_cali = stmt_total_cali.where(
                Calificacion.cargado_por == cargado_por
            )
        result = await self.session.execute(stmt_total_cali)
        total_calificaciones = result.scalar() or 0

        # Actividades with counts
        stmt_actividades = (
            select(
                Calificacion.actividad,
                func.count().label("total_alumnos"),
                func.count()
                .filter(Calificacion.aprobado == True)  # noqa: E712
                .label("total_aprobados"),
            )
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
            )
            .group_by(Calificacion.actividad)
        )
        if cargado_por is not None:
            stmt_actividades = stmt_actividades.where(
                Calificacion.cargado_por == cargado_por
            )
        result = await self.session.execute(stmt_actividades)
        actividades_raw = result.all()

        actividades = [
            {
                "nombre": row[0],
                "total_alumnos": row[1],
                "total_aprobados": row[2],
            }
            for row in actividades_raw
        ]

        return {
            "total_alumnos": total_alumnos,
            "alumnos_con_calificaciones": alumnos_con_calificaciones,
            "total_aprobadas": total_aprobadas,
            "total_calificaciones": total_calificaciones,
            "actividades": actividades,
        }
