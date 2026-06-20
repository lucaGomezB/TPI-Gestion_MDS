"""Router for admin role management endpoints.

Protected with ``require_permission("usuario:gestionar")``.

Endpoints:
- GET /api/admin/roles — list all roles
- GET /api/admin/roles/{id} — get single role
- POST /api/admin/roles — create role
- PUT /api/admin/roles/{id} — update role
- DELETE /api/admin/roles/{id} — soft-delete role
- GET /api/admin/permissions — list all available permissions
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.permissions import ALL_PERMISSIONS, PERMISSIONS_BY_MODULE
from app.core.unit_of_work import UnitOfWork
from app.schemas.admin_roles import (
    ModuloPermisos,
    PermissionsResponse,
    RolCreate,
    RolResponse,
    RolUpdate,
)
from app.services.admin_roles import AdminRolesService

router = APIRouter(tags=["admin-roles"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


PERM_GESTIONAR = "usuario:gestionar"


# ── GET /api/admin/permissions ──────────────────────────────────────────────


@router.get(
    "/api/admin/permissions",
    status_code=HTTP_200_OK,
    response_model=PermissionsResponse,
)
async def list_permissions(
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> PermissionsResponse:
    """List all available permissions grouped by module.

    Used by the frontend Roles page to render permission checkboxes.
    """
    modulos = [
        ModuloPermisos(modulo=mod, permisos=perms)
        for mod, perms in PERMISSIONS_BY_MODULE.items()
    ]
    todos = sorted(ALL_PERMISSIONS)
    return PermissionsResponse(modulos=modulos, todos=todos)


# ── GET /api/admin/roles ────────────────────────────────────────────────────


@router.get(
    "/api/admin/roles",
    status_code=HTTP_200_OK,
    response_model=list[RolResponse],
)
async def list_roles(
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[RolResponse]:
    """List all active roles with their permissions."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AdminRolesService(uow)
        return await service.list_roles()


# ── GET /api/admin/roles/{id} ────────────────────────────────────────────────


@router.get(
    "/api/admin/roles/{id}",
    status_code=HTTP_200_OK,
    response_model=RolResponse,
)
async def get_role(
    id: str,
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> RolResponse:
    """Get a single role by ID, including its permissions."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AdminRolesService(uow)
        return await service.get_role(id)


# ── POST /api/admin/roles ────────────────────────────────────────────────────


@router.post(
    "/api/admin/roles",
    status_code=HTTP_201_CREATED,
    response_model=RolResponse,
)
async def create_role(
    body: RolCreate,
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> RolResponse:
    """Create a new role with permissions."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AdminRolesService(uow)
        return await service.create_role(body)


# ── PUT /api/admin/roles/{id} ────────────────────────────────────────────────


@router.put(
    "/api/admin/roles/{id}",
    status_code=HTTP_200_OK,
    response_model=RolResponse,
)
async def update_role(
    id: str,
    body: RolUpdate,
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> RolResponse:
    """Update a role. Only provided fields are changed.

    Use ``"activo": false`` to soft-delete, ``"activo": true`` to reactivate.
    Use ``"permisos": [...]`` to replace all permission assignments.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AdminRolesService(uow)
        return await service.update_role(id, body)


# ── DELETE /api/admin/roles/{id} ─────────────────────────────────────────────


@router.delete(
    "/api/admin/roles/{id}",
    status_code=HTTP_204_NO_CONTENT,
)
async def delete_role(
    id: str,
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> None:
    """Soft-delete a role. Fails if the role is currently assigned to users."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AdminRolesService(uow)
        await service.delete_role(id)
