"""Router for salary grid endpoints — base salary, plus salary, and subject groups.

All endpoints are protected with ``require_permission("liquidaciones:configurar-salarios")``.

Endpoints:
- POST/GET/PUT /api/admin/salarios/base — SalarioBase CRUD
- POST/GET/PUT /api/admin/salarios/plus — SalarioPlus CRUD
- POST/GET/PUT /api/admin/salarios/grupos — GrupoMateria CRUD
- GET /api/admin/salarios/grupos/{id}/materias — materia assignments
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.grilla_salarial import (
    GrupoMateriaCreate,
    GrupoMateriaResponse,
    GrupoMateriaUpdate,
    MateriaGrupoResponse,
    MateriasAsignarRequest,
    SalarioBaseCreate,
    SalarioBaseResponse,
    SalarioBaseUpdate,
    SalarioPlusCreate,
    SalarioPlusResponse,
    SalarioPlusUpdate,
)
from app.services.grilla_salarial import (
    GrupoMateriaService,
    SalarioBaseService,
    SalarioPlusService,
)

router = APIRouter(tags=["salary-grid"])


PERMISSION = "liquidaciones:configurar-salarios"


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


# ── SalarioBase endpoints ───────────────────────────────────────────────


@router.post(
    "/api/admin/salarios/base",
    status_code=HTTP_201_CREATED,
    response_model=SalarioBaseResponse,
)
async def create_salario_base(
    body: SalarioBaseCreate,
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioBaseResponse:
    """Create a new salary base entry."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = SalarioBaseService(uow)
        return await service.create(body)


@router.get(
    "/api/admin/salarios/base",
    response_model=list[SalarioBaseResponse],
)
async def list_salario_base(
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SalarioBaseResponse]:
    """List all salary base entries for the current tenant."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = SalarioBaseService(uow)
        return await service.list()


@router.get(
    "/api/admin/salarios/base/{id}",
    response_model=SalarioBaseResponse,
)
async def get_salario_base(
    id: str,
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioBaseResponse:
    """Get a single salary base entry by ID."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = SalarioBaseService(uow)
        return await service.get(id)


@router.put(
    "/api/admin/salarios/base/{id}",
    response_model=SalarioBaseResponse,
)
async def update_salario_base(
    id: str,
    body: SalarioBaseUpdate,
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioBaseResponse:
    """Update a salary base entry."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = SalarioBaseService(uow)
        return await service.update(id, body)


# ── SalarioPlus endpoints ───────────────────────────────────────────────


@router.post(
    "/api/admin/salarios/plus",
    status_code=HTTP_201_CREATED,
    response_model=SalarioPlusResponse,
)
async def create_salario_plus(
    body: SalarioPlusCreate,
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioPlusResponse:
    """Create a new salary plus entry."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = SalarioPlusService(uow)
        return await service.create(body)


@router.get(
    "/api/admin/salarios/plus",
    response_model=list[SalarioPlusResponse],
)
async def list_salario_plus(
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SalarioPlusResponse]:
    """List all salary plus entries for the current tenant."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = SalarioPlusService(uow)
        return await service.list()


@router.get(
    "/api/admin/salarios/plus/{id}",
    response_model=SalarioPlusResponse,
)
async def get_salario_plus(
    id: str,
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioPlusResponse:
    """Get a single salary plus entry by ID."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = SalarioPlusService(uow)
        return await service.get(id)


@router.put(
    "/api/admin/salarios/plus/{id}",
    response_model=SalarioPlusResponse,
)
async def update_salario_plus(
    id: str,
    body: SalarioPlusUpdate,
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioPlusResponse:
    """Update a salary plus entry."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = SalarioPlusService(uow)
        return await service.update(id, body)


# ── GrupoMateria endpoints ──────────────────────────────────────────────


@router.post(
    "/api/admin/salarios/grupos",
    status_code=HTTP_201_CREATED,
    response_model=GrupoMateriaResponse,
)
async def create_grupo_materia(
    body: GrupoMateriaCreate,
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GrupoMateriaResponse:
    """Create a new subject group."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = GrupoMateriaService(uow)
        return await service.create(body)


@router.get(
    "/api/admin/salarios/grupos",
    response_model=list[GrupoMateriaResponse],
)
async def list_grupos_materia(
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[GrupoMateriaResponse]:
    """List all subject groups for the current tenant."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = GrupoMateriaService(uow)
        return await service.list()


@router.get(
    "/api/admin/salarios/grupos/{id}",
    response_model=GrupoMateriaResponse,
)
async def get_grupo_materia(
    id: str,
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GrupoMateriaResponse:
    """Get a single subject group by ID."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = GrupoMateriaService(uow)
        return await service.get(id)


@router.put(
    "/api/admin/salarios/grupos/{id}",
    response_model=GrupoMateriaResponse,
)
async def update_grupo_materia(
    id: str,
    body: GrupoMateriaUpdate,
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GrupoMateriaResponse:
    """Update a subject group."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = GrupoMateriaService(uow)
        return await service.update(id, body)


# ── Materia assignment endpoints ────────────────────────────────────────


@router.get(
    "/api/admin/salarios/grupos/{id}/materias",
    response_model=list[MateriaGrupoResponse],
)
async def get_materias_by_grupo(
    id: str,
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MateriaGrupoResponse]:
    """Get all materias assigned to a group."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = GrupoMateriaService(uow)
        return await service.get_materias_by_grupo(id)


@router.put(
    "/api/admin/salarios/grupos/{id}/materias",
    response_model=list[MateriaGrupoResponse],
)
async def assign_materias_to_grupo(
    id: str,
    body: MateriasAsignarRequest,
    _: Annotated[None, Depends(require_permission(PERMISSION))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MateriaGrupoResponse]:
    """Assign materias to a group (replace semantics)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = GrupoMateriaService(uow)
        return await service.assign_materias(id, body.materia_ids)
