"""Router for guardia management endpoints.

Endpoints:
- POST /api/materias/{id}/guardias — registro de guardia (F6.6)
- GET /api/materias/{id}/guardias — consulta con filtros (F6.6)
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.guardias import GuardiaCreate, GuardiaResponse
from app.services.guardias import GuardiaService

router = APIRouter(tags=["guardias"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


# ── Registrar guardia ────────────────────────────────────────────────────────


@router.post(
    "/api/materias/{materia_id}/guardias",
    status_code=HTTP_201_CREATED,
    response_model=GuardiaResponse,
)
async def registrar_guardia(
    materia_id: str,
    body: GuardiaCreate,
    _: Annotated[None, Depends(require_permission("guardias:registrar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuardiaResponse:
    """Register a new guardia record (F6.6)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = GuardiaService(uow)
        return await service.registrar_guardia(body)


# ── Consultar guardias ───────────────────────────────────────────────────────


@router.get(
    "/api/materias/{materia_id}/guardias",
    status_code=HTTP_200_OK,
)
async def listar_guardias(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("guardias:ver_todas"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    estado: str | None = Query(None),
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
) -> dict:
    """List guardias with optional filters (F6.6)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = GuardiaService(uow)
        items = await service.listar_guardias(
            materia_id=materia_id,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        return {
            "total": len(items),
            "items": [i.model_dump() for i in items],
        }
