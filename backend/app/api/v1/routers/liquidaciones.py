"""Router for liquidaciones endpoints — period view, detail, close, history.

All endpoints are protected with ``require_permission`` for the appropriate
liquidaciones permission (ver, calcular, cerrar).

Endpoints:
- GET /api/admin/liquidaciones — period view with KPIs
- GET /api/admin/liquidaciones/{id} — individual detail with desglose
- POST /api/admin/liquidaciones/{id}/cerrar — close (inmutabilize)
- GET /api/admin/liquidaciones/historial — closed settlement history
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.liquidacion import (
    LiquidacionDetailResponse,
    LiquidacionListResponse,
    LiquidacionResponse,
)
from app.services.liquidacion import LiquidacionService

router = APIRouter(tags=["liquidaciones"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


PERM_VER = "liquidaciones:ver"
PERM_CALCULAR = "liquidaciones:calcular"
PERM_CERRAR = "liquidaciones:cerrar"


# ── GET /api/admin/liquidaciones — Period view ──────────────────────────


@router.get(
    "/api/admin/liquidaciones",
    status_code=HTTP_200_OK,
    response_model=LiquidacionListResponse,
)
async def get_liquidaciones(
    periodo: Annotated[str, Query(min_length=7, max_length=7, description="Period in YYYY-MM")],
    cohorte_id: Annotated[str | None, Query(description="Filter by cohorte")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    _: Annotated[None, Depends(require_permission(PERM_VER))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> LiquidacionListResponse:
    """Get liquidaciones for a period with KPI headers."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = LiquidacionService(uow, actor_id=current_user.get("id"))
        return await service.get_periodo_view(
            periodo=periodo,
            cohorte_id=cohorte_id,
            page=page,
            page_size=page_size,
        )


# ── GET /api/admin/liquidaciones/historial — History ────────────────────


@router.get(
    "/api/admin/liquidaciones/historial",
    status_code=HTTP_200_OK,
    response_model=LiquidacionListResponse,
)
async def get_liquidaciones_historial(
    periodo: Annotated[str | None, Query(min_length=7, max_length=7, description="Filter by period YYYY-MM")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    _: Annotated[None, Depends(require_permission(PERM_VER))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> LiquidacionListResponse:
    """Get history of closed liquidaciones."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = LiquidacionService(uow, actor_id=current_user.get("id"))
        return await service.get_historial(
            periodo=periodo,
            page=page,
            page_size=page_size,
        )


# ── GET /api/admin/liquidaciones/{id} — Detail ──────────────────────────


@router.get(
    "/api/admin/liquidaciones/{id}",
    status_code=HTTP_200_OK,
    response_model=LiquidacionDetailResponse,
)
async def get_liquidacion_detail(
    id: str,
    _: Annotated[None, Depends(require_permission(PERM_VER))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> LiquidacionDetailResponse:
    """Get detailed view of a single liquidacion."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = LiquidacionService(uow, actor_id=current_user.get("id"))
        return await service.get_detail(id)


# ── POST /api/admin/liquidaciones/{id}/cerrar — Close ───────────────────


@router.post(
    "/api/admin/liquidaciones/{id}/cerrar",
    status_code=HTTP_200_OK,
    response_model=LiquidacionResponse,
)
async def cerrar_liquidacion(
    id: str,
    _: Annotated[None, Depends(require_permission(PERM_CERRAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> LiquidacionResponse:
    """Close a liquidacion (inmutabilize per RN-22)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = LiquidacionService(uow, actor_id=current_user.get("id"))
        return await service.cerrar(id)
