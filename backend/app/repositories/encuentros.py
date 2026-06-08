"""Repositories for SlotEncuentro and InstanciaEncuentro entities.

Provides tenant-scoped CRUD with support for slot-based instance generation
and filtered queries by materia and slot.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro


class SlotEncuentroRepository:
    """Tenant-scoped CRUD for SlotEncuentro."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, data: dict) -> SlotEncuentro:
        """Create a new SlotEncuentro with tenant_id auto-assigned."""
        data.setdefault("tenant_id", self.tenant_id)
        instance = SlotEncuentro(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, id: str) -> SlotEncuentro | None:
        """Get a SlotEncuentro by ID, scoped to tenant."""
        result = await self.session.execute(
            select(SlotEncuentro).where(
                SlotEncuentro.id == id,
                SlotEncuentro.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_materia(self, materia_id: str) -> list[SlotEncuentro]:
        """List slots for a materia within the tenant."""
        result = await self.session.execute(
            select(SlotEncuentro).where(
                SlotEncuentro.tenant_id == self.tenant_id,
                SlotEncuentro.materia_id == materia_id,
            )
        )
        return list(result.scalars().all())

    async def list(self) -> list[SlotEncuentro]:
        """List all slots for the tenant."""
        result = await self.session.execute(
            select(SlotEncuentro).where(SlotEncuentro.tenant_id == self.tenant_id)
        )
        return list(result.scalars().all())

    async def update(self, id: str, data: dict) -> SlotEncuentro | None:
        """Update a SlotEncuentro, scoped to tenant."""
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance


class InstanciaEncuentroRepository:
    """Tenant-scoped CRUD for InstanciaEncuentro."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, data: dict) -> InstanciaEncuentro:
        """Create a new InstanciaEncuentro with tenant_id auto-assigned."""
        data.setdefault("tenant_id", self.tenant_id)
        instance = InstanciaEncuentro(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def bulk_create(self, instances_data: list[dict]) -> list[InstanciaEncuentro]:
        """Create multiple InstanciaEncuentro records in bulk."""
        instances = []
        for data in instances_data:
            data.setdefault("tenant_id", self.tenant_id)
            instance = InstanciaEncuentro(**data)
            self.session.add(instance)
            instances.append(instance)
        await self.session.flush()
        return instances

    async def get_by_id(self, id: str) -> InstanciaEncuentro | None:
        """Get an InstanciaEncuentro by ID, scoped to tenant."""
        result = await self.session.execute(
            select(InstanciaEncuentro).where(
                InstanciaEncuentro.id == id,
                InstanciaEncuentro.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_slot(self, slot_id: str) -> list[InstanciaEncuentro]:
        """List instances generated from a specific slot."""
        result = await self.session.execute(
            select(InstanciaEncuentro).where(
                InstanciaEncuentro.tenant_id == self.tenant_id,
                InstanciaEncuentro.slot_id == slot_id,
            )
            .order_by(InstanciaEncuentro.fecha)
        )
        return list(result.scalars().all())

    async def list_by_materia(
        self,
        materia_id: str,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[InstanciaEncuentro]:
        """List instances for a materia with optional filters."""
        stmt = select(InstanciaEncuentro).where(
            InstanciaEncuentro.tenant_id == self.tenant_id,
            InstanciaEncuentro.materia_id == materia_id,
        )
        if estado is not None:
            stmt = stmt.where(InstanciaEncuentro.estado == estado)
        if fecha_desde is not None:
            stmt = stmt.where(InstanciaEncuentro.fecha >= fecha_desde)
        if fecha_hasta is not None:
            stmt = stmt.where(InstanciaEncuentro.fecha <= fecha_hasta)
        stmt = stmt.order_by(InstanciaEncuentro.fecha)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list(self) -> list[InstanciaEncuentro]:
        """List all instances for the tenant."""
        result = await self.session.execute(
            select(InstanciaEncuentro).where(
                InstanciaEncuentro.tenant_id == self.tenant_id
            )
            .order_by(InstanciaEncuentro.fecha)
        )
        return list(result.scalars().all())

    async def update(self, id: str, data: dict) -> InstanciaEncuentro | None:
        """Update an InstanciaEncuentro, scoped to tenant."""
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance
