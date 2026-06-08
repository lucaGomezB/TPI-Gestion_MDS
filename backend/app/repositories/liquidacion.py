"""LiquidacionRepository — CRUD for salary settlements with pagination and filtering.

Provides:
- ``find_by_periodo`` — paginated period view with optional cohorte filter
- ``find_by_id`` — single record lookup
- ``find_historial`` — paginated closed-settlement history
- ``create`` — create a new liquidacion
- ``save`` — persist state changes (e.g., close)
- ``find_by_unique_key`` — check for duplicate (cohorte, usuario, periodo)
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.liquidacion import EstadoLiquidacion, Liquidacion
from app.repositories.base import BaseRepository


class LiquidacionRepository(BaseRepository[Liquidacion]):
    """Tenant-scoped CRUD for Liquidacion.

    Since Liquidacion does NOT inherit AuditMixin (D-03: custom estado),
    the BaseRepository's soft-delete filter does not apply — all records
    are always visible.
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = Liquidacion

    # ── Period view ───────────────────────────────────────────────────

    async def find_by_periodo(
        self,
        periodo: str,
        cohorte_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Liquidacion], int]:
        """Return paginated liquidaciones for a period, with optional cohorte filter.

        Returns:
            Tuple of (items, total_count).
        """
        model = self.model_class
        base_stmt = select(model).where(
            model.tenant_id == self.tenant_id,
            model.periodo == periodo,
        )
        if cohorte_id is not None:
            base_stmt = base_stmt.where(model.cohorte_id == cohorte_id)

        # Count total
        count_stmt = select(model.id).where(
            model.tenant_id == self.tenant_id,
            model.periodo == periodo,
        )
        if cohorte_id is not None:
            count_stmt = count_stmt.where(model.cohorte_id == cohorte_id)
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.all())

        # Paginate
        offset = (page - 1) * page_size
        stmt = base_stmt.order_by(model.usuario_id).offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    # ── Single record ─────────────────────────────────────────────────

    async def find_by_id(self, id: str) -> Liquidacion | None:
        """Return a single liquidacion by ID, scoped by tenant."""
        model = self.model_class
        stmt = select(model).where(
            model.id == id,
            model.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── History ───────────────────────────────────────────────────────

    async def find_historial(
        self,
        periodo: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Liquidacion], int]:
        """Return paginated closed liquidaciones, ordered by cerrada_at desc."""
        model = self.model_class
        base_stmt = select(model).where(
            model.tenant_id == self.tenant_id,
            model.estado == EstadoLiquidacion.CERRADA.value,
        )
        if periodo is not None:
            base_stmt = base_stmt.where(model.periodo == periodo)

        # Count
        count_stmt = select(model.id).where(
            model.tenant_id == self.tenant_id,
            model.estado == EstadoLiquidacion.CERRADA.value,
        )
        if periodo is not None:
            count_stmt = count_stmt.where(model.periodo == periodo)
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.all())

        # Paginate
        offset = (page - 1) * page_size
        stmt = base_stmt.order_by(model.cerrada_at.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    # ── Write operations ─────────────────────────────────────────────

    async def create(self, data: dict) -> Liquidacion:
        """Create a new Liquidacion record.

        Returns:
            The created Liquidacion instance (flushed, not committed).
        """
        data.setdefault("tenant_id", self.tenant_id)
        instance = Liquidacion(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def save(self, liquidacion: Liquidacion) -> Liquidacion:
        """Persist changes to an existing Liquidacion.

        Flushes the session so changes are visible within the UoW.
        """
        await self.session.flush()
        return liquidacion

    # ── Duplicate check ──────────────────────────────────────────────

    async def find_by_unique_key(
        self,
        cohorte_id: str,
        usuario_id: str,
        periodo: str,
    ) -> Liquidacion | None:
        """Check if a liquidacion already exists for (cohorte, usuario, periodo).

        Used to avoid duplicate calculations (RN-37).
        """
        model = self.model_class
        stmt = select(model).where(
            model.tenant_id == self.tenant_id,
            model.cohorte_id == cohorte_id,
            model.usuario_id == usuario_id,
            model.periodo == periodo,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
