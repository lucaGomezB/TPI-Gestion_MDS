"""Router for internal messaging endpoints (C-13).

Endpoints:
- GET /api/mensajes — list inbox (authenticated)
- GET /api/mensajes/{id} — view thread (authenticated)
- POST /api/mensajes — send message (requires mensajeria:enviar)
- POST /api/mensajes/{id}/responder — reply in thread (authenticated)
- GET /api/mensajes/no-leidos — unread count (authenticated)

All endpoints require authentication. Sending requires additional permission.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.mensaje import (
    HiloResponse,
    InboxResponse,
    MensajeCreatedResponse,
    MensajeCreate,
    MensajeResponder,
    NoLeidosResponse,
)
from app.services.mensajeria import MensajeService

router = APIRouter(tags=["mensajeria"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


@router.get(
    "/api/mensajes",
    response_model=InboxResponse,
    status_code=HTTP_200_OK,
)
async def listar_inbox(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> InboxResponse:
    """List the authenticated user's inbox.

    Returns paginated thread summaries ordered by most recent message.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = MensajeService(uow, current_user)
        return await service.listar_inbox(limit=limit, offset=offset)


@router.get(
    "/api/mensajes/no-leidos",
    response_model=NoLeidosResponse,
    status_code=HTTP_200_OK,
)
async def contar_no_leidos(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> NoLeidosResponse:
    """Get the unread message count for the authenticated user."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = MensajeService(uow, current_user)
        return await service.contar_no_leidos()


@router.get(
    "/api/mensajes/{id}",
    response_model=HiloResponse,
    status_code=HTTP_200_OK,
)
async def ver_hilo(
    id: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> HiloResponse:
    """View a complete message thread.

    Auto-marks unread messages as read for the current user.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = MensajeService(uow, current_user)
        return await service.ver_hilo(id)


@router.post(
    "/api/mensajes",
    response_model=MensajeCreatedResponse,
    status_code=HTTP_201_CREATED,
)
async def enviar_mensaje(
    body: MensajeCreate,
    _: Annotated[None, Depends(require_permission("mensajeria:enviar"))],
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> MensajeCreatedResponse:
    """Send a message to another user in the same tenant.

    Creates a new thread or reuses an existing one with the same subject.
    Requires the ``mensajeria:enviar`` permission.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = MensajeService(uow, current_user)
        return await service.enviar(body)


@router.post(
    "/api/mensajes/{id}/responder",
    response_model=MensajeCreatedResponse,
    status_code=HTTP_201_CREATED,
)
async def responder_mensaje(
    id: str,
    body: MensajeResponder,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> MensajeCreatedResponse:
    """Reply within an existing message thread.

    The ``id`` references an existing message to identify the thread.
    The current user must be a participant in the thread.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = MensajeService(uow, current_user)
        return await service.responder(id, body)
