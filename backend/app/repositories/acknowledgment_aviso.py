"""AcknowledgmentRepository — tenant-scoped CRUD for acknowledgment records.

Supports:
- Idempotent find by aviso + usuario for safe retries (RN-19)
- Count by aviso for admin detail view
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.repositories.base import BaseRepository


class AcknowledgmentRepository(BaseRepository[AcknowledgmentAviso]):
    """Tenant-scoped CRUD for AcknowledgmentAviso records."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = AcknowledgmentAviso

    async def find_by_aviso_and_user(
        self,
        aviso_id: str,
        usuario_id: str,
    ) -> AcknowledgmentAviso | None:
        """Find an acknowledgment by aviso and user (idempotency check).

        Args:
            aviso_id: Aviso UUID.
            usuario_id: Usuario UUID.

        Returns:
            Existing AcknowledgmentAviso or None.
        """
        model = self.model_class
        stmt = (
            select(model)
            .where(
                model.aviso_id == aviso_id,
                model.usuario_id == usuario_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_aviso(self, aviso_id: str) -> int:
        """Count acknowledgments for a specific aviso.

        Args:
            aviso_id: Aviso UUID.

        Returns:
            Total acknowledgment count.
        """
        model = self.model_class
        stmt = (
            select(func.count())
            .select_from(model)
            .where(model.aviso_id == aviso_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
