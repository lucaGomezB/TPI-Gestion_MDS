"""Repository for notas-finales queries (F2.5).

Provides tenant-scoped queries that aggregate Calificacion records
grouped by entrada_padron_id for a materia, with optional filters.

Design (per C-10 design.md):
- D1: Repository returns raw data; service layer calculates final grades.
- D7: Separate repository from export/monitor capabilities.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.calificaciones import Calificacion
from app.models.padron import EntradaPadron, VersionPadron


class ReportesNotasRepository:
    """Tenant-scoped repository for notas-finales queries.

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

    async def get_calificaciones_agrupadas(
        self,
        materia_id: str,
        cargado_por: str | None = None,
        comision: str | None = None,
        busqueda: str | None = None,
    ) -> list[dict]:
        """Get all calificaciones grouped by entrada_padron_id for a materia.

        Args:
            materia_id: The materia UUID.
            cargado_por: If set (PROFESOR), scope to this user's grades.
            comision: Optional filter by comision name.
            busqueda: Optional ILIKE search on nombre/apellidos.

        Returns:
            A list of dicts with student data and their calificaciones.
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

        # Eager load calificaciones with optional scope filter
        cali_loader = joinedload(EntradaPadron.calificaciones)
        cali_loader = cali_loader.where(Calificacion.materia_id == materia_id)
        if cargado_por is not None:
            cali_loader = cali_loader.where(
                Calificacion.cargado_por == cargado_por
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
