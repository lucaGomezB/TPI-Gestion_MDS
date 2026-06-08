"""Service layer for salary grid — business rules and validation.

Encapsulates:
- Overlap validation for temporal vigencias (RN-31)
- Base salary CRUD with role validation (RN-32)
- Plus salary CRUD with grupo validation (RN-33)
- GrupoMateria CRUD with materia assignment
- Public query methods for C-19 (liquidaciones)
"""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.core.unit_of_work import UnitOfWork
from app.models.grilla_salarial import (
    GrupoMateria,
    MateriaGrupo,
    RolSalarial,
    SalarioBase,
    SalarioPlus,
)
from app.schemas.grilla_salarial import (
    GrupoMateriaCreate,
    GrupoMateriaResponse,
    GrupoMateriaUpdate,
    MateriaGrupoResponse,
    SalarioBaseCreate,
    SalarioBaseResponse,
    SalarioBaseUpdate,
    SalarioPlusCreate,
    SalarioPlusResponse,
    SalarioPlusUpdate,
)


# ── Mapping helpers ─────────────────────────────────────────────────────


def _base_to_response(instance: SalarioBase) -> SalarioBaseResponse:
    return SalarioBaseResponse(
        id=instance.id,
        tenant_id=instance.tenant_id,
        rol=instance.rol,
        monto=float(instance.monto),
        desde=str(instance.desde),
        hasta=str(instance.hasta) if instance.hasta else None,
        created_at=instance.created_at.isoformat() if hasattr(instance.created_at, "isoformat") else str(instance.created_at),
        updated_at=instance.updated_at.isoformat() if hasattr(instance.updated_at, "isoformat") else str(instance.updated_at),
    )


def _plus_to_response(instance: SalarioPlus) -> SalarioPlusResponse:
    return SalarioPlusResponse(
        id=instance.id,
        tenant_id=instance.tenant_id,
        grupo=instance.grupo,
        rol=instance.rol,
        descripcion=instance.descripcion,
        monto=float(instance.monto),
        desde=str(instance.desde),
        hasta=str(instance.hasta) if instance.hasta else None,
        created_at=instance.created_at.isoformat() if hasattr(instance.created_at, "isoformat") else str(instance.created_at),
        updated_at=instance.updated_at.isoformat() if hasattr(instance.updated_at, "isoformat") else str(instance.updated_at),
    )


def _grupo_to_response(instance: GrupoMateria) -> GrupoMateriaResponse:
    return GrupoMateriaResponse(
        id=instance.id,
        tenant_id=instance.tenant_id,
        grupo=instance.grupo,
        descripcion=instance.descripcion,
        created_at=instance.created_at.isoformat() if hasattr(instance.created_at, "isoformat") else str(instance.created_at),
        updated_at=instance.updated_at.isoformat() if hasattr(instance.updated_at, "isoformat") else str(instance.updated_at),
    )


def _mg_to_response(instance: MateriaGrupo) -> MateriaGrupoResponse:
    return MateriaGrupoResponse(
        id=instance.id,
        materia_id=instance.materia_id,
        grupo_id=instance.grupo_id,
        tenant_id=instance.tenant_id,
        created_at=instance.created_at.isoformat() if hasattr(instance.created_at, "isoformat") else str(instance.created_at),
    )


# ── SalarioBaseService ──────────────────────────────────────────────────


class SalarioBaseService:
    """Business logic for SalarioBase CRUD with overlap validation."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.repo = uow.salario_base

    async def create(self, data: SalarioBaseCreate) -> SalarioBaseResponse:
        """Create a new SalarioBase entry after overlap validation.

        Raises:
            HTTPException(409): If the entry overlaps an existing one for the same role.
        """
        # Validate overlap
        has_overlap = await self.repo.check_overlap(
            rol=data.rol,
            desde=data.desde,
            hasta=data.hasta,
        )
        if has_overlap:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=(
                    f"Overlapping vigencia: there is already an active SalarioBase "
                    f"for rol '{data.rol}' in the date range {data.desde} to {data.hasta or '∞'}"
                ),
            )

        instance = await self.repo.create(data.model_dump())
        return _base_to_response(instance)

    async def get(self, id: str) -> SalarioBaseResponse:
        """Get a single SalarioBase by ID.

        Raises:
            HTTPException(404): If not found.
        """
        instance = await self.repo.get(id)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"SalarioBase[{id}] not found",
            )
        return _base_to_response(instance)

    async def list(self) -> list[SalarioBaseResponse]:
        """List all SalarioBase entries for the current tenant, ordered by desde desc."""
        model = self.repo.model_class
        instances = await self.repo.list()
        instances.sort(key=lambda x: x.desde, reverse=True)
        return [_base_to_response(i) for i in instances]

    @staticmethod
    async def get_vigentes_for_date(
        uow: UnitOfWork, target_date: date
    ) -> dict:
        """Return all vigente base and plus records for a given date.

        Consumed by C-19 (liquidaciones) to compute salary amounts.

        Args:
            uow: Active unit of work with tenant context.
            target_date: The date to query vigencia for.

        Returns:
            Dict with:
            - bases: list of SalarioBaseResponse per rol (max 1 per rol)
            - plus: list of SalarioPlusResponse for matching grupo+rol combos
        """
        bases: list[SalarioBaseResponse] = []
        for rol in RolSalarial:
            instance = await uow.salario_base.get_vigente_for_rol(
                rol=rol.value, target_date=target_date
            )
            if instance is not None:
                bases.append(_base_to_response(instance))

        all_plus = await uow.salario_plus.get_all_vigentes_for_date(
            target_date
        )
        plus_responses = [_plus_to_response(p) for p in all_plus]

        return {"bases": bases, "plus": plus_responses}

    async def update(
        self, id: str, data: SalarioBaseUpdate
    ) -> SalarioBaseResponse:
        """Update a SalarioBase entry.

        Raises:
            HTTPException(404): If not found.
            HTTPException(409): If the update would cause overlap.
        """
        existing = await self.repo.get(id)
        if existing is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"SalarioBase[{id}] not found",
            )

        update_data = data.model_dump(exclude_unset=True)

        # Check overlap if dates or rol changed
        rol = update_data.get("rol", existing.rol)
        desde = update_data.get("desde", existing.desde)
        hasta = update_data.get("hasta", existing.hasta)

        has_overlap = await self.repo.check_overlap(
            rol=rol,
            desde=desde,
            hasta=hasta,
            exclude_id=id,
        )
        if has_overlap:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=(
                    f"Overlapping vigencia: the update would create an overlap "
                    f"for rol '{rol}' in the date range {desde} to {hasta or '∞'}"
                ),
            )

        instance = await self.repo.update(id, update_data)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"SalarioBase[{id}] not found",
            )
        return _base_to_response(instance)


# ── SalarioPlusService ──────────────────────────────────────────────────


class SalarioPlusService:
    """Business logic for SalarioPlus CRUD with overlap validation."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.repo = uow.salario_plus

    async def create(self, data: SalarioPlusCreate) -> SalarioPlusResponse:
        """Create a new SalarioPlus entry after overlap validation.

        Raises:
            HTTPException(409): If overlapping entry exists for same (grupo, rol).
        """
        has_overlap = await self.repo.check_overlap(
            grupo=data.grupo,
            rol=data.rol,
            desde=data.desde,
            hasta=data.hasta,
        )
        if has_overlap:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=(
                    f"Overlapping vigencia: there is already an active SalarioPlus "
                    f"for (grupo='{data.grupo}', rol='{data.rol}') "
                    f"in the date range {data.desde} to {data.hasta or '∞'}"
                ),
            )

        instance = await self.repo.create(data.model_dump())
        return _plus_to_response(instance)

    async def get(self, id: str) -> SalarioPlusResponse:
        """Get a single SalarioPlus by ID."""
        instance = await self.repo.get(id)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"SalarioPlus[{id}] not found",
            )
        return _plus_to_response(instance)

    async def list(self) -> list[SalarioPlusResponse]:
        """List all SalarioPlus entries for the current tenant, ordered by desde desc."""
        instances = await self.repo.list()
        instances.sort(key=lambda x: x.desde, reverse=True)
        return [_plus_to_response(i) for i in instances]

    async def update(
        self, id: str, data: SalarioPlusUpdate
    ) -> SalarioPlusResponse:
        """Update a SalarioPlus entry.

        Raises:
            HTTPException(404): If not found.
            HTTPException(409): If the update would cause overlap.
        """
        existing = await self.repo.get(id)
        if existing is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"SalarioPlus[{id}] not found",
            )

        update_data = data.model_dump(exclude_unset=True)

        grupo = update_data.get("grupo", existing.grupo)
        rol = update_data.get("rol", existing.rol)
        desde = update_data.get("desde", existing.desde)
        hasta = update_data.get("hasta", existing.hasta)

        has_overlap = await self.repo.check_overlap(
            grupo=grupo,
            rol=rol,
            desde=desde,
            hasta=hasta,
            exclude_id=id,
        )
        if has_overlap:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=(
                    f"Overlapping vigencia: the update would create an overlap "
                    f"for (grupo='{grupo}', rol='{rol}') "
                    f"in the date range {desde} to {hasta or '∞'}"
                ),
            )

        instance = await self.repo.update(id, update_data)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"SalarioPlus[{id}] not found",
            )
        return _plus_to_response(instance)


# ── GrupoMateriaService ─────────────────────────────────────────────────


class GrupoMateriaService:
    """Business logic for GrupoMateria CRUD and materia assignment."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.repo = uow.grupo_materia

    async def create(self, data: GrupoMateriaCreate) -> GrupoMateriaResponse:
        """Create a new GrupoMateria entry.

        Raises:
            HTTPException(409): If the grupo key already exists for this tenant.
        """
        # Check for duplicate key
        existing = await self.repo.list(grupo=data.grupo)
        if existing:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"GrupoMateria with key '{data.grupo}' already exists for this tenant",
            )

        instance = await self.repo.create(data.model_dump(exclude_unset=True))
        return _grupo_to_response(instance)

    async def get(self, id: str) -> GrupoMateriaResponse:
        """Get a single GrupoMateria by ID."""
        instance = await self.repo.get(id)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"GrupoMateria[{id}] not found",
            )
        return _grupo_to_response(instance)

    async def list(self) -> list[GrupoMateriaResponse]:
        """List all GrupoMateria entries for the current tenant."""
        instances = await self.repo.list()
        return [_grupo_to_response(i) for i in instances]

    async def update(
        self, id: str, data: GrupoMateriaUpdate
    ) -> GrupoMateriaResponse:
        """Update a GrupoMateria entry.

        Raises:
            HTTPException(404): If not found.
        """
        existing = await self.repo.get(id)
        if existing is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"GrupoMateria[{id}] not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return _grupo_to_response(existing)

        instance = await self.repo.update(id, update_data)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"GrupoMateria[{id}] not found",
            )
        return _grupo_to_response(instance)

    async def assign_materias(
        self, grupo_id: str, materia_ids: list[str]
    ) -> list[MateriaGrupoResponse]:
        """Assign materias to a group (replace semantics).

        Raises:
            HTTPException(404): If the group does not exist.
        """
        grupo = await self.repo.get(grupo_id)
        if grupo is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"GrupoMateria[{grupo_id}] not found",
            )

        result = await self.repo.assign_materias(grupo_id, materia_ids)
        return [_mg_to_response(r) for r in result]

    async def get_materias_by_grupo(
        self, grupo_id: str
    ) -> list[MateriaGrupoResponse]:
        """Get all materias assigned to a group."""
        grupo = await self.repo.get(grupo_id)
        if grupo is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"GrupoMateria[{grupo_id}] not found",
            )

        result = await self.repo.get_materias_by_grupo(grupo_id)
        return [_mg_to_response(r) for r in result]
