"""Router for admin user management endpoints.

Protected with ``require_permission("usuario:gestionar")``.

Endpoints:
- GET /api/admin/usuarios — list users, optional ``?rol=`` filter
- GET /api/admin/usuarios/{id} — get single user
- POST /api/admin/usuarios — create user
- PUT /api/admin/usuarios/{id} — update user
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.admin_usuarios import (
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)
from app.services.admin_usuarios import AdminUsuariosService

router = APIRouter(tags=["admin-usuarios"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


PERM_GESTIONAR = "usuario:gestionar"


# ── GET /api/admin/usuarios ────────────────────────────────────────────────


@router.get(
    "/api/admin/usuarios",
    status_code=HTTP_200_OK,
    response_model=list[UsuarioResponse],
)
async def list_usuarios(
    rol: Annotated[str | None, Query(description="Filter by role name (e.g. 'docente', 'PROFESOR')")] = None,
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[UsuarioResponse]:
    """List active users, optionally filtered by role name."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AdminUsuariosService(uow)
        return await service.list_users(rol=rol)


# ── GET /api/admin/usuarios/{id} ────────────────────────────────────────────


@router.get(
    "/api/admin/usuarios/{id}",
    status_code=HTTP_200_OK,
    response_model=UsuarioResponse,
)
async def get_usuario(
    id: str,
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> UsuarioResponse:
    """Get a single user by ID, including their role names."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AdminUsuariosService(uow)
        return await service.get_user(id)


# ── POST /api/admin/usuarios ────────────────────────────────────────────────


@router.post(
    "/api/admin/usuarios",
    status_code=HTTP_201_CREATED,
    response_model=UsuarioResponse,
)
async def create_usuario(
    body: UsuarioCreate,
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> UsuarioResponse:
    """Create a new user with role assignments."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AdminUsuariosService(uow)
        return await service.create_user(body)


# ── PUT /api/admin/usuarios/{id} ────────────────────────────────────────────


@router.put(
    "/api/admin/usuarios/{id}",
    status_code=HTTP_200_OK,
    response_model=UsuarioResponse,
)
async def update_usuario(
    id: str,
    body: UsuarioUpdate,
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> UsuarioResponse:
    """Update a user. Only provided fields are changed.

    Use ``"activo": false`` to soft-delete, ``"activo": true`` to reactivate.
    Use ``"roles": [...]`` to replace all role assignments.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AdminUsuariosService(uow)
        return await service.update_user(id, body)
