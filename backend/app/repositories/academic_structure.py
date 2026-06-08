"""Repositories for academic structure entities.

Provides tenant-scoped CRUD for Carrera, Cohorte, Materia, and ProgramaMateria.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.programa_materia import ProgramaMateria


class CarreraRepository:
    """Tenant-scoped CRUD for Carrera."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, data: dict) -> Carrera:
        """Create a new Carrera with tenant_id auto-assigned."""
        data.setdefault("tenant_id", self.tenant_id)
        instance = Carrera(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, id: str) -> Carrera | None:
        """Get a Carrera by ID, scoped to tenant."""
        result = await self.session.execute(
            select(Carrera).where(
                Carrera.id == id,
                Carrera.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list(self) -> list[Carrera]:
        """List all Carreras for the tenant."""
        result = await self.session.execute(
            select(Carrera).where(Carrera.tenant_id == self.tenant_id)
        )
        return list(result.scalars().all())

    async def update(self, id: str, data: dict) -> Carrera | None:
        """Update a Carrera, scoped to tenant."""
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def find_by_codigo(self, codigo: str) -> Carrera | None:
        """Find a Carrera by codigo within the tenant."""
        result = await self.session.execute(
            select(Carrera).where(
                Carrera.tenant_id == self.tenant_id,
                Carrera.codigo == codigo,
            )
        )
        return result.scalar_one_or_none()

    async def count_active_cohortes(self, carrera_id: str) -> int:
        """Count active cohortes for a carrera."""
        from app.models.mixins import EstadoAcademico

        result = await self.session.execute(
            select(Cohorte).where(
                Cohorte.carrera_id == carrera_id,
                Cohorte.tenant_id == self.tenant_id,
                Cohorte.estado == EstadoAcademico.ACTIVA,
            )
        )
        return len(result.scalars().all())


class CohorteRepository:
    """Tenant-scoped CRUD for Cohorte."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, data: dict) -> Cohorte:
        """Create a new Cohorte with tenant_id auto-assigned."""
        data.setdefault("tenant_id", self.tenant_id)
        instance = Cohorte(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, id: str) -> Cohorte | None:
        """Get a Cohorte by ID, scoped to tenant."""
        result = await self.session.execute(
            select(Cohorte).where(
                Cohorte.id == id,
                Cohorte.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_carrera(self, carrera_id: str | None = None) -> list[Cohorte]:
        """List cohortes for the tenant, optionally filtered by carrera_id."""
        stmt = select(Cohorte).where(Cohorte.tenant_id == self.tenant_id)
        if carrera_id is not None:
            stmt = stmt.where(Cohorte.carrera_id == carrera_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: str, data: dict) -> Cohorte | None:
        """Update a Cohorte, scoped to tenant."""
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def find_by_nombre_in_carrera(
        self, nombre: str, carrera_id: str
    ) -> Cohorte | None:
        """Find a Cohorte by nombre within a carrera and tenant."""
        result = await self.session.execute(
            select(Cohorte).where(
                Cohorte.tenant_id == self.tenant_id,
                Cohorte.carrera_id == carrera_id,
                Cohorte.nombre == nombre,
            )
        )
        return result.scalar_one_or_none()


class MateriaRepository:
    """Tenant-scoped CRUD for Materia."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, data: dict) -> Materia:
        """Create a new Materia with tenant_id auto-assigned."""
        data.setdefault("tenant_id", self.tenant_id)
        instance = Materia(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, id: str) -> Materia | None:
        """Get a Materia by ID, scoped to tenant."""
        result = await self.session.execute(
            select(Materia).where(
                Materia.id == id,
                Materia.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list(self) -> list[Materia]:
        """List all Materias for the tenant."""
        result = await self.session.execute(
            select(Materia).where(Materia.tenant_id == self.tenant_id)
        )
        return list(result.scalars().all())

    async def update(self, id: str, data: dict) -> Materia | None:
        """Update a Materia, scoped to tenant."""
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def find_by_codigo(self, codigo: str) -> Materia | None:
        """Find a Materia by codigo within the tenant."""
        result = await self.session.execute(
            select(Materia).where(
                Materia.tenant_id == self.tenant_id,
                Materia.codigo == codigo,
            )
        )
        return result.scalar_one_or_none()


class ProgramaMateriaRepository:
    """Tenant-scoped CRUD for ProgramaMateria."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, data: dict) -> ProgramaMateria:
        """Create a new ProgramaMateria with tenant_id auto-assigned."""
        data.setdefault("tenant_id", self.tenant_id)
        instance = ProgramaMateria(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, id: str) -> ProgramaMateria | None:
        """Get a ProgramaMateria by ID, scoped to tenant."""
        result = await self.session.execute(
            select(ProgramaMateria).where(
                ProgramaMateria.id == id,
                ProgramaMateria.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_filters(self, **filters: Any) -> list[ProgramaMateria]:
        """List ProgramaMateria with optional equality filters.

        Args:
            **filters: Optional filters (materia_id, carrera_id, cohorte_id).
        """
        stmt = select(ProgramaMateria).where(
            ProgramaMateria.tenant_id == self.tenant_id
        )
        for attr, value in filters.items():
            column = getattr(ProgramaMateria, attr, None)
            if column is not None and value is not None:
                stmt = stmt.where(column == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, id: str) -> bool:
        """Hard delete a ProgramaMateria record.

        Returns:
            True if deleted, False if not found.
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
