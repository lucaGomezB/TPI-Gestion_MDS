"""Repository for Guardia entity.

Provides tenant-scoped CRUD with filtering by materia, estado, and date range.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardia import Guardia


class GuardiaRepository:
    """Tenant-scoped CRUD for Guardia."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, data: dict) -> Guardia:
        """Create a new Guardia with tenant_id auto-assigned."""
        data.setdefault("tenant_id", self.tenant_id)
        instance = Guardia(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, id: str) -> Guardia | None:
        """Get a Guardia by ID, scoped to tenant."""
        result = await self.session.execute(
            select(Guardia).where(
                Guardia.id == id,
                Guardia.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_materia(
        self,
        materia_id: str,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[Guardia]:
        """List guardias for a materia with optional filters."""
        stmt = select(Guardia).where(
            Guardia.tenant_id == self.tenant_id,
            Guardia.materia_id == materia_id,
        )
        if estado is not None:
            stmt = stmt.where(Guardia.estado == estado)
        if fecha_desde is not None:
            stmt = stmt.where(Guardia.creada_at >= fecha_desde)
        if fecha_hasta is not None:
            stmt = stmt.where(Guardia.creada_at <= fecha_hasta)
        stmt = stmt.order_by(Guardia.creada_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list(self) -> list[Guardia]:
        """List all guardias for the tenant."""
        result = await self.session.execute(
            select(Guardia).where(Guardia.tenant_id == self.tenant_id)
            .order_by(Guardia.creada_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, id: str, data: dict) -> Guardia | None:
        """Update a Guardia, scoped to tenant."""
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance
