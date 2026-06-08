"""Router for admin facturas endpoints — admin view and abonar lifecycle.

Protected with ``require_permission("facturas:gestionar")``.

Endpoints:
- GET /api/admin/facturas — admin view with filters (F10.5)
- GET /api/admin/facturas/{id}/descargar — download PDF file
- PUT /api/admin/facturas/{id}/abonar — mark as Abonada
"""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.factura import FacturaDetailResponse, FacturaListResponse, FacturaResponse
from app.services.factura import FacturaService

router = APIRouter(tags=["admin-facturas"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


PERM_GESTIONAR = "facturas:gestionar"


# ── GET /api/admin/facturas — Admin view (F10.5) ────────────────────────


@router.get(
    "/api/admin/facturas",
    status_code=HTTP_200_OK,
    response_model=FacturaListResponse,
)
async def get_admin_facturas(
    estado: Annotated[str | None, Query(description="Filter by estado (Pendiente|Abonada)")] = None,
    periodo: Annotated[str | None, Query(min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$", description="Filter by YYYY-MM")] = None,
    usuario_id: Annotated[str | None, Query(description="Filter by usuario_id")] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=200, description="Search in detalle")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> FacturaListResponse:
    """Get admin view of all facturas with combinable filters."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = FacturaService(uow, actor_id=current_user.get("id"))
        return await service.get_admin_view(
            estado=estado,
            periodo=periodo,
            usuario_id=usuario_id,
            q=q,
            page=page,
            page_size=page_size,
        )


# ── GET /api/admin/facturas/{id}/descargar — Download PDF ──────────────


@router.get(
    "/api/admin/facturas/{id}/descargar",
    status_code=HTTP_200_OK,
    response_class=FileResponse,
)
async def descargar_factura(
    id: str,
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> FileResponse:
    """Download the PDF file associated with a factura.

    Returns the file as application/pdf. Requires facturas:gestionar.
    Raises 404 if factura not found or file not found on disk.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = FacturaService(uow, actor_id=current_user.get("id"))
        factura = await service.get_factura(id)
        file_path = factura.referencia_archivo

        if not os.path.exists(file_path):
            from fastapi import HTTPException
            from starlette.status import HTTP_404_NOT_FOUND
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="PDF file not found on storage",
            )

        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=os.path.basename(file_path),
        )


# ── PUT /api/admin/facturas/{id}/abonar — Mark as paid ──────────────────


@router.put(
    "/api/admin/facturas/{id}/abonar",
    status_code=HTTP_200_OK,
    response_model=FacturaResponse | FacturaDetailResponse,
)
async def abonar_factura(
    id: str,
    descargar: Annotated[bool, Query(description="Include download URL")] = False,
    _: Annotated[None, Depends(require_permission(PERM_GESTIONAR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> FacturaResponse | FacturaDetailResponse:
    """Mark a factura as Abonada.

    Sets estado=Abonada and abonada_at=now().
    Returns 409 if already Abonada, 404 if not found.
    Use ``?descargar=true`` to include the PDF download URL.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = FacturaService(uow, actor_id=current_user.get("id"))
        return await service.abonar(id, descargar=descargar)
