"""Router for admin avisos CRUD endpoints (C-12).

Endpoints:
- POST /api/admin/avisos — create aviso
- GET /api/admin/avisos — list with filters
- GET /api/admin/avisos/{id} — detail with ack count
- PUT /api/admin/avisos/{id} — update aviso
- DELETE /api/admin/avisos/{id} — deactivate aviso

All endpoints require ``avisos:publicar`` permission (COORDINADOR, ADMIN).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.aviso import (
    AvisoCreate,
    AvisoListResponse,
    AvisoResponse,
    AvisoUpdate,
)
from app.services.aviso import AvisoService

router = APIRouter(tags=["avisos-admin"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


@router.post(
    "/api/admin/avisos",
    response_model=AvisoResponse,
    status_code=HTTP_201_CREATED,
)
async def create_aviso(
    body: AvisoCreate,
    _: Annotated[None, Depends(require_permission("avisos:publicar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvisoResponse:
    """Create a new aviso (admin only)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AvisoService(uow, current_user)
        return await service.create_aviso(body)


@router.get(
    "/api/admin/avisos",
    response_model=AvisoListResponse,
    status_code=HTTP_200_OK,
)
async def list_avisos_admin(
    activo: Annotated[bool | None, Query()] = None,
    alcance: Annotated[str | None, Query()] = None,
    severidad: Annotated[str | None, Query()] = None,
    _: Annotated[None, Depends(require_permission("avisos:publicar"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AvisoListResponse:
    """List avisos with optional filters (admin only)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AvisoService(uow, current_user)
        return await service.list_avisos_admin(
            activo=activo,
            alcance=alcance,
            severidad=severidad,
        )


@router.get(
    "/api/admin/avisos/{id}",
    response_model=AvisoResponse,
    status_code=HTTP_200_OK,
)
async def get_aviso_detail(
    id: str,
    _: Annotated[None, Depends(require_permission("avisos:publicar"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AvisoResponse:
    """Get aviso detail with acknowledgment count (admin only)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AvisoService(uow, current_user)
        return await service.get_aviso_detail(id)


@router.put(
    "/api/admin/avisos/{id}",
    response_model=AvisoResponse,
    status_code=HTTP_200_OK,
)
async def update_aviso(
    id: str,
    body: AvisoUpdate,
    _: Annotated[None, Depends(require_permission("avisos:publicar"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AvisoResponse:
    """Update an existing aviso (admin only)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AvisoService(uow, current_user)
        return await service.update_aviso(id, body)


@router.delete(
    "/api/admin/avisos/{id}",
    status_code=HTTP_204_NO_CONTENT,
)
async def deactivate_aviso(
    id: str,
    _: Annotated[None, Depends(require_permission("avisos:publicar"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> Response:
    """Deactivate an aviso (sets activo=false, admin only)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AvisoService(uow, current_user)
        await service.deactivate_aviso(id)
        return Response(status_code=HTTP_204_NO_CONTENT)
