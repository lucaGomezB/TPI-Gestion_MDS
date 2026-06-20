"""Repository for FechaEvaluacion entity.

Provides tenant-scoped CRUD via BaseRepository with a custom
list_by_filters method supporting optional materia_id and cohorte_id filters.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fecha_evaluacion import FechaEvaluacion
from app.repositories.base import BaseRepository


class EvaluacionRepository(BaseRepository[FechaEvaluacion]):
    """Tenant-scoped CRUD for FechaEvaluacion with filtered list support.

    Inherits standard CRUD operations (get, create, update, soft_delete)
    from BaseRepository with automatic tenant scoping and soft-delete
    filtering via AuditMixin.
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = FechaEvaluacion

    async def list_by_filters(
        self,
        materia_id: str | None = None,
        cohorte_id: str | None = None,
    ) -> list[FechaEvaluacion]:
        """List evaluations with optional materia and cohorte filters.

        Results are automatically scoped to the tenant and exclude
        soft-deleted records (estado = 'Inactivo') via BaseRepository._stmt().

        Args:
            materia_id: Optional materia UUID to filter by.
            cohorte_id: Optional cohorte UUID to filter by.

        Returns:
            List of FechaEvaluacion instances ordered by fecha ascending.
        """
        stmt = self._stmt()
        if materia_id is not None:
            stmt = stmt.where(FechaEvaluacion.materia_id == materia_id)
        if cohorte_id is not None:
            stmt = stmt.where(FechaEvaluacion.cohorte_id == cohorte_id)
        stmt = stmt.order_by(FechaEvaluacion.fecha.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
