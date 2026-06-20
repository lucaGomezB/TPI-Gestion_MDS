"""Repository for monitor and seguimiento queries (F2.7-F2.9).

Provides tenant-scoped queries for cross-subject activity monitoring
and per-subject student seguimiento.

Design (per C-10 design.md):
- D3: Single repository with JOIN-heavy queries for monitor general.
- D4: Seguimiento endpoint with role-aware scope.
- D7: Separate repository for monitor-specific queries.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.calificaciones import Calificacion
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.padron import EntradaPadron, VersionPadron


class ReportesMonitorRepository:
    """Tenant-scoped repository for monitor and seguimiento queries.

    Args:
        session: An active SQLAlchemy ``AsyncSession``.
        tenant_id: The tenant UUID string for data isolation.
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    # ── Monitor General (F2.7) ──────────────────────────────────────────

    async def get_monitor_general(
        self,
        materia_id: str | None = None,
        regional: str | None = None,
        comision: str | None = None,
        estado_actividad: str | None = None,
        busqueda: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        """Get cross-subject activity status for all students.

        Returns consolidated data with per-student activity metrics
        across all subjects in the tenant.

        Args:
            materia_id: Optional filter by materia.
            regional: Optional filter by student regional.
            comision: Optional filter by comision.
            estado_actividad: Optional filter by "pendiente" or "completo".
            busqueda: Optional ILIKE search on nombre/apellidos.
            fecha_desde: Optional date range start.
            fecha_hasta: Optional date range end.

        Returns:
            A list of dicts with monitor entry data.
        """
        # Get all active versions for the tenant
        version_stmt = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.activa == True,  # noqa: E712
            )
        )
        versions = await self.session.execute(version_stmt)
        version_list = list(versions.scalars().all())
        if not version_list:
            return []

        version_materia_map = {v.id: v.materia_id for v in version_list}
        version_cohorte_map = {v.id: v.cohorte_id for v in version_list}
        version_ids = list(version_materia_map.keys())

        # Filter by materia_id if provided
        if materia_id is not None:
            version_ids = [
                v.id for v in version_list
                if v.materia_id == materia_id
            ]
            if not version_ids:
                return []

        # Get all EntradaPadron for the filtered versions
        ep_stmt = (
            select(EntradaPadron)
            .where(
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.version_id.in_(version_ids),
            )
        )
        if comision:
            ep_stmt = ep_stmt.where(EntradaPadron.comision == comision)
        if regional:
            ep_stmt = ep_stmt.where(EntradaPadron.regional == regional)
        if busqueda:
            pattern = f"%{busqueda}%"
            ep_stmt = ep_stmt.where(
                EntradaPadron.nombre.ilike(pattern)
                | EntradaPadron.apellidos.ilike(pattern)
            )

        # Eager load calificaciones for each entrada
        cali_loader = joinedload(EntradaPadron.calificaciones)
        if fecha_desde is not None:
            cali_loader = cali_loader.where(
                Calificacion.importado_at >= fecha_desde
            )
        if fecha_hasta is not None:
            cali_loader = cali_loader.where(
                Calificacion.importado_at <= fecha_hasta
            )
        ep_stmt = ep_stmt.options(cali_loader)

        entries = await self.session.execute(ep_stmt)
        entrada_list = list(entries.scalars().all())

        # Also get materia names
        materia_ids = list(set(version_materia_map[v] for v in version_ids if v in version_materia_map))
        if materia_ids:
            mat_stmt = (
                select(Materia)
                .where(
                    Materia.tenant_id == self.tenant_id,
                    Materia.id.in_(materia_ids),
                )
            )
            mat_result = await self.session.execute(mat_stmt)
            materias = {m.id: m.nombre for m in list(mat_result.scalars().all())}
        else:
            materias = {}

        # Also get cohorte names
        cohorte_ids = list(set(version_cohorte_map[v] for v in version_ids if v in version_cohorte_map))
        if cohorte_ids:
            coh_stmt = (
                select(Cohorte)
                .where(
                    Cohorte.tenant_id == self.tenant_id,
                    Cohorte.id.in_(cohorte_ids),
                )
            )
            coh_result = await self.session.execute(coh_stmt)
            cohortes = {c.id: c.nombre for c in list(coh_result.scalars().all())}
        else:
            cohortes = {}

        # Build result dicts
        result: list[dict] = []
        for entry in entrada_list:
            version_id = entry.version_id
            mat_id = version_materia_map.get(version_id, "")
            mat_nombre = materias.get(mat_id, "")
            coh_id = version_cohorte_map.get(version_id, "")
            coh_nombre = cohortes.get(coh_id, "")

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

            total_actividades = len(calificaciones)
            total_aprobadas = sum(1 for c in calificaciones if c["aprobado"])
            total_pendientes = total_actividades - total_aprobadas

            # Find last activity date
            fechas = [
                c["importado_at"] for c in calificaciones
                if c["importado_at"] is not None
            ]
            ultima_actividad = (
                max(fechas).isoformat() if fechas else None
            )

            item = {
                "entrada_padron_id": entry.id,
                "nombre": entry.nombre,
                "apellidos": entry.apellidos,
                "comision": entry.comision,
                "regional": entry.regional,
                "materia_nombre": mat_nombre,
                "materia_id": mat_id,
                "cohorte_nombre": coh_nombre,
                "total_actividades": total_actividades,
                "total_aprobadas": total_aprobadas,
                "total_pendientes": total_pendientes,
                "ultima_actividad": ultima_actividad,
            }

            # Apply estado_actividad filter
            if estado_actividad == "pendiente" and total_pendientes == 0:
                continue
            if estado_actividad == "completo" and total_pendientes > 0:
                continue

            result.append(item)

        return result

    async def get_metricas_generales(
        self,
    ) -> dict:
        """Get top-level aggregated metrics for the tenant.

        Returns:
            A dict with total_alumnos, total_materias, total_actividades,
            total_aprobadas.
        """
        # Total active materias
        mat_stmt = (
            select(func.count())
            .select_from(Materia)
            .where(Materia.tenant_id == self.tenant_id)
        )
        mat_result = await self.session.execute(mat_stmt)
        total_materias = mat_result.scalar() or 0

        # Total calificaciones in tenant
        cali_stmt = (
            select(func.count())
            .select_from(Calificacion)
            .where(Calificacion.tenant_id == self.tenant_id)
        )
        cali_result = await self.session.execute(cali_stmt)
        total_actividades = cali_result.scalar() or 0

        # Total aprobadas
        aprob_stmt = (
            select(func.count())
            .select_from(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.aprobado == True,  # noqa: E712
            )
        )
        aprob_result = await self.session.execute(aprob_stmt)
        total_aprobadas = aprob_result.scalar() or 0

        # Total distinct alumnos in active padron
        alum_stmt = (
            select(func.count(func.distinct(EntradaPadron.id)))
            .select_from(EntradaPadron)
            .where(EntradaPadron.tenant_id == self.tenant_id)
        )
        alum_result = await self.session.execute(alum_stmt)
        total_alumnos = alum_result.scalar() or 0

        return {
            "total_alumnos": total_alumnos,
            "total_materias": total_materias,
            "total_actividades": total_actividades,
            "total_aprobadas": total_aprobadas,
        }

    # ── Seguimiento (F2.8, F2.9) ───────────────────────────────────────

    async def get_seguimiento(
        self,
        materia_id: str,
        cargado_por: str | None = None,
        comision: str | None = None,
        regional: str | None = None,
        actividad: str | None = None,
        minimo_actividades_cumplidas: int | None = None,
        busqueda: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        """Get per-student seguimiento data for a materia.

        Args:
            materia_id: The materia UUID.
            cargado_por: If set (PROFESOR), scope to this user's grades.
            comision: Optional filter by comision.
            regional: Optional filter by regional.
            actividad: Optional filter by activity name.
            minimo_actividades_cumplidas: Min approved activities (HAVING).
            busqueda: Optional ILIKE search on nombre/apellidos.
            fecha_desde: Optional date range start (COORDINADOR/ADMIN only).
            fecha_hasta: Optional date range end (COORDINADOR/ADMIN only).

        Returns:
            A list of dicts with seguimiento data.
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
        if regional:
            stmt = stmt.where(EntradaPadron.regional == regional)
        if busqueda:
            pattern = f"%{busqueda}%"
            stmt = stmt.where(
                EntradaPadron.nombre.ilike(pattern)
                | EntradaPadron.apellidos.ilike(pattern)
            )

        # Eager load calificaciones with filters
        cali_loader = joinedload(EntradaPadron.calificaciones)
        cali_loader = cali_loader.where(
            Calificacion.materia_id == materia_id,
        )
        if cargado_por is not None:
            cali_loader = cali_loader.where(
                Calificacion.cargado_por == cargado_por
            )
        if actividad is not None:
            cali_loader = cali_loader.where(
                Calificacion.actividad == actividad
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
                }
                for c in entry.calificaciones
            ]

            total_aprobadas = sum(1 for c in calificaciones if c["aprobado"])
            total_actividades = len(calificaciones)

            # Apply minimo_actividades_cumplidas filter
            if (
                minimo_actividades_cumplidas is not None
                and total_aprobadas < minimo_actividades_cumplidas
            ):
                continue

            alumnos.append({
                "entrada_padron_id": entry.id,
                "nombre": entry.nombre,
                "apellidos": entry.apellidos,
                "comision": entry.comision,
                "regional": entry.regional,
                "calificaciones": calificaciones,
                "total_actividades": total_actividades,
                "total_aprobadas": total_aprobadas,
            })

        return alumnos

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
