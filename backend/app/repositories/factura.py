"""FacturaRepository — CRUD for teacher invoices with pagination and filtering.

Provides:
- ``create`` — create a new factura
- ``find_by_id`` — single record lookup scoped by tenant
- ``find_by_usuario`` — paginated per-teacher history with optional periodo filter
- ``find_all`` — admin view with combinable filters (estado, periodo, usuario, q)
- ``save`` — persist state changes (e.g., abonar)
"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factura import Factura
from app.repositories.base import BaseRepository


class FacturaRepository(BaseRepository[Factura]):
    """Tenant-scoped CRUD for Factura.

    Since Factura does NOT inherit AuditMixin (D-03: custom estado),
    the BaseRepository's soft-delete filter does not apply — all records
    are always visible.
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = Factura

    # ── Single record ─────────────────────────────────────────────────

    async def find_by_id(self, id: str) -> Factura | None:
        """Return a single factura by ID, scoped by tenant."""
        model = self.model_class
        stmt = select(model).where(
            model.id == id,
            model.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Per-usuario history ───────────────────────────────────────────

    async def find_by_usuario(
        self,
        usuario_id: str,
        periodo: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Factura], int]:
        """Return paginated facturas for a specific usuario.

        Args:
            usuario_id: The user's UUID.
            periodo: Optional YYYY-MM filter.
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Tuple of (items, total_count).
        """
        model = self.model_class
        base_stmt = select(model).where(
            model.tenant_id == self.tenant_id,
            model.usuario_id == usuario_id,
        )
        if periodo is not None:
            base_stmt = base_stmt.where(model.periodo == periodo)

        # Count
        count_stmt = select(model.id).where(
            model.tenant_id == self.tenant_id,
            model.usuario_id == usuario_id,
        )
        if periodo is not None:
            count_stmt = count_stmt.where(model.periodo == periodo)
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.all())

        # Paginate
        offset = (page - 1) * page_size
        stmt = base_stmt.order_by(model.cargada_at.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    # ── Admin view with combinable filters ────────────────────────────

    async def find_all(
        self,
        estado: str | None = None,
        periodo: str | None = None,
        usuario_id: str | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Factura], int]:
        """Return paginated facturas for admin view with combinable filters.

        All filters are optional and applied as AND conditions.

        Args:
            estado: Filter by estado (Pendiente/Abonada).
            periodo: Filter by YYYY-MM period.
            usuario_id: Filter by specific usuario.
            q: Full-text search on detalle (LIKE %q%).
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Tuple of (items, total_count).
        """
        model = self.model_class
        base_stmt = select(model).where(
            model.tenant_id == self.tenant_id,
        )

        if estado is not None:
            base_stmt = base_stmt.where(model.estado == estado)
        if periodo is not None:
            base_stmt = base_stmt.where(model.periodo == periodo)
        if usuario_id is not None:
            base_stmt = base_stmt.where(model.usuario_id == usuario_id)
        if q is not None and q.strip():
            base_stmt = base_stmt.where(
                or_(
                    model.detalle.ilike(f"%{q.strip()}%"),
                    model.periodo.ilike(f"%{q.strip()}%"),
                )
            )

        # Count
        count_stmt = select(model.id).where(
            model.tenant_id == self.tenant_id,
        )
        if estado is not None:
            count_stmt = count_stmt.where(model.estado == estado)
        if periodo is not None:
            count_stmt = count_stmt.where(model.periodo == periodo)
        if usuario_id is not None:
            count_stmt = count_stmt.where(model.usuario_id == usuario_id)
        if q is not None and q.strip():
            count_stmt = count_stmt.where(
                or_(
                    model.detalle.ilike(f"%{q.strip()}%"),
                    model.periodo.ilike(f"%{q.strip()}%"),
                )
            )
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.all())

        # Paginate
        offset = (page - 1) * page_size
        stmt = base_stmt.order_by(model.cargada_at.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    # ── Write operations ─────────────────────────────────────────────

    async def create(self, data: dict) -> Factura:
        """Create a new Factura record.

        Returns:
            The created Factura instance (flushed, not committed).
        """
        data.setdefault("tenant_id", self.tenant_id)
        instance = Factura(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def save(self, factura: Factura) -> Factura:
        """Persist changes to an existing Factura.

        Flushes the session so changes are visible within the UoW.
        """
        await self.session.flush()
        return factura
