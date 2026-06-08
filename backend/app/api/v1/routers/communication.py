"""Router for communications queue endpoints (C-11).

Endpoints:
- POST /api/materias/{id}/comunicaciones/preview — preview templates (RN-16)
- POST /api/materias/{id}/comunicaciones/enviar — enqueue bulk send
- GET /api/materias/{id}/comunicaciones — list lotes for materia
- GET /api/materias/{id}/comunicaciones/{lote_id} — lote detail
- PUT /api/admin/comunicaciones/{id}/aprobar — approve/reject (RN-17)
- PUT /api/comunicaciones/{id}/cancelar — cancel own pending communication

Permission guards:
- ``comunicacion:enviar`` for preview, enqueue, list
- ``comunicacion:aprobar`` for approve/reject
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.communication import (
    AprobarRequest,
    AprobarResponse,
    ComunicacionResponse,
    EnviarRequest,
    LoteResponse,
    PreviewRequest,
    PreviewResponse,
)
from app.services.communication import CommunicationService

router = APIRouter(tags=["communication"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


# ── Preview (RN-16) ──────────────────────────────────────────────────────


@router.post(
    "/api/materias/{id}/comunicaciones/preview",
    response_model=PreviewResponse,
    status_code=HTTP_200_OK,
)
async def preview_comunicacion(
    id: str,
    body: PreviewRequest,
    _: Annotated[None, Depends(require_permission("comunicacion:enviar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PreviewResponse:
    """Preview rendered email templates for sample students."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CommunicationService(uow, current_user)
        return await service.preview_comunicacion(id, body)


# ── Enqueue (RN-16, RN-17) ───────────────────────────────────────────────


@router.post(
    "/api/materias/{id}/comunicaciones/enviar",
    response_model=LoteResponse,
    status_code=HTTP_201_CREATED,
)
async def enviar_comunicacion(
    id: str,
    body: EnviarRequest,
    _: Annotated[None, Depends(require_permission("comunicacion:enviar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoteResponse:
    """Enqueue a bulk communication for sending."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CommunicationService(uow, current_user)
        return await service.enqueue_comunicacion(id, body)


# ── List lotes for materia ───────────────────────────────────────────────


@router.get(
    "/api/materias/{id}/comunicaciones",
    response_model=list[LoteResponse],
    status_code=HTTP_200_OK,
)
async def listar_comunicaciones(
    id: str,
    _: Annotated[None, Depends(require_permission("comunicacion:enviar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[LoteResponse]:
    """List all communication batches for a materia."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CommunicationService(uow, current_user)
        return await service.listar_comunicaciones(id)


# ── Lote detail ──────────────────────────────────────────────────────────


@router.get(
    "/api/materias/{id}/comunicaciones/{lote_id}",
    response_model=LoteResponse,
    status_code=HTTP_200_OK,
)
async def get_lote_detail(
    id: str,
    lote_id: str,
    _: Annotated[None, Depends(require_permission("comunicacion:enviar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoteResponse:
    """Get detail for a specific communication batch."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CommunicationService(uow, current_user)
        return await service.get_lote_detail(id, lote_id)


# ── Approve/Reject (RN-17) ───────────────────────────────────────────────


@router.put(
    "/api/admin/comunicaciones/{id}/aprobar",
    response_model=AprobarResponse,
    status_code=HTTP_200_OK,
)
async def aprobar_comunicacion(
    id: str,
    body: AprobarRequest,
    _: Annotated[None, Depends(require_permission("comunicacion:aprobar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AprobarResponse:
    """Approve or reject a pending bulk communication."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CommunicationService(uow, current_user)
        result = await service.aprobar_comunicacion(id, body)
        return AprobarResponse(**result)


# ── Cancel single communication ──────────────────────────────────────────


@router.put(
    "/api/comunicaciones/{id}/cancelar",
    response_model=ComunicacionResponse,
    status_code=HTTP_200_OK,
)
async def cancelar_comunicacion(
    id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComunicacionResponse:
    """Cancel a pending communication."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CommunicationService(uow, current_user)
        return await service.cancelar_comunicacion(id)
