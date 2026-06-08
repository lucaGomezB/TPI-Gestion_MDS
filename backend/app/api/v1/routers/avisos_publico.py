"""Router for public avisos endpoints (C-12).

Endpoints:
- GET /api/avisos — visible avisos for authenticated user (RN-18, RN-20)
- POST /api/avisos/{id}/ack — acknowledge reading an aviso (RN-19)

Permission guards:
- ``avisos:ver`` for GET endpoints
- ``avisos:ack`` for POST ack endpoint
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.aviso import AckResponse, AvisoResponse
from app.services.aviso import AvisoService

router = APIRouter(tags=["avisos"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


@router.get(
    "/api/avisos",
    response_model=list[AvisoResponse],
    status_code=HTTP_200_OK,
)
async def list_avisos_visibles(
    severidad: Annotated[str | None, Query()] = None,
    _: Annotated[None, Depends(require_permission("avisos:ver"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[AvisoResponse]:
    """Get avisos visible to the authenticated user (RN-18, RN-20)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AvisoService(uow, current_user)
        return await service.list_avisos_visibles(severidad=severidad)


@router.post(
    "/api/avisos/{id}/ack",
    response_model=AckResponse,
    status_code=HTTP_200_OK,
)
async def acknowledge_aviso(
    id: str,
    _: Annotated[None, Depends(require_permission("avisos:ack"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AckResponse:
    """Acknowledge reading an aviso (RN-19)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AvisoService(uow, current_user)
        return await service.acknowledge_aviso(id)
