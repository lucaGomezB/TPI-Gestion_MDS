"""Repository for export-atrasados queries (F2.6).

Provides tenant-scoped queries to detect potentially uncorrected
practical assignments (TPs) based on RN-07/RN-08 heuristics.

Design (per C-10 design.md):
- D2: Uses available Calificacion data as heuristic (F1.2 not yet available).
- D7: Separate repository for export-specific queries.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificaciones import Calificacion
from app.models.padron import EntradaPadron, VersionPadron


class ReportesExportRepository:
    """Tenant-scoped repository for export-atrasados queries.

    Args:
        session: An active SQLAlchemy ``AsyncSession``.
        tenant_id: The tenant UUID string for data isolation.
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

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

    async def get_actividades_textuales(
        self,
        materia_id: str,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[str]:
        """Get distinct textual activity names for a materia.

        Only activities with at least one Calificacion where
        ``nota_textual IS NOT NULL`` are returned (RN-08 filter).

        Args:
            materia_id: The materia UUID.
            fecha_desde: Optional date range start.
            fecha_hasta: Optional date range end.

        Returns:
            A list of distinct activity names with textual grades.
        """
        stmt = (
            select(Calificacion.actividad)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.nota_textual.isnot(None),
            )
            .distinct()
        )
        if fecha_desde is not None:
            stmt = stmt.where(Calificacion.importado_at >= fecha_desde)
        if fecha_hasta is not None:
            stmt = stmt.where(Calificacion.importado_at <= fecha_hasta)

        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_alumnos_sin_calificacion_textual(
        self,
        materia_id: str,
        actividades_textuales: list[str],
        comision: str | None = None,
    ) -> list[dict]:
        """Get students without textual Calificacion for specific activities.

        Returns students from the active padron who lack a Calificacion
        record with ``nota_textual`` for any of the given textual activities.

        Args:
            materia_id: The materia UUID.
            actividades_textuales: List of textual activity names to check.
            comision: Optional filter by comision name.

        Returns:
            A list of dicts with student data and their calificaciones.
        """
        version = await self._get_active_version(materia_id)
        if version is None or not actividades_textuales:
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

        from sqlalchemy.orm import joinedload

        cali_loader = joinedload(EntradaPadron.calificaciones)
        cali_loader = cali_loader.where(
            Calificacion.materia_id == materia_id,
            Calificacion.actividad.in_(actividades_textuales),
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
            alumnos.append({
                "entrada_padron_id": entry.id,
                "nombre": entry.nombre,
                "apellidos": entry.apellidos,
                "comision": entry.comision,
                "calificaciones": calificaciones,
            })

        return alumnos
