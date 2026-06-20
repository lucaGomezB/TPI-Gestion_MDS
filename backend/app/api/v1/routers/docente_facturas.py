"""Router for docente facturas endpoints — upload, own history, and download.

Protected with ``require_permission("facturas:subir")``.

Endpoints:
- POST /api/docentes/facturas — upload invoice PDF (RF-61)
- GET /api/docentes/facturas — own history list
- GET /api/docentes/facturas/{id}/descargar — download own invoice PDF
"""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.factura import FacturaListResponse, FacturaResponse
from app.services.factura import FacturaService

router = APIRouter(tags=["docente-facturas"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


PERM_SUBIR = "facturas:subir"


# ── POST /api/docentes/facturas — Upload PDF (RF-61) ────────────────────


@router.post(
    "/api/docentes/facturas",
    status_code=HTTP_201_CREATED,
    response_model=FacturaResponse,
)
async def subir_factura(
    periodo: Annotated[str, Form(min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$")],
    detalle: Annotated[str, Form(max_length=500)],
    archivo: Annotated[UploadFile, File(description="PDF invoice file")],
    _: Annotated[None, Depends(require_permission(PERM_SUBIR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> FacturaResponse:
    """Upload a new invoice PDF.

    Only users with ``facturador=true`` are allowed.
    File must be a valid PDF, max 10 MB.
    """
    content = await archivo.read()
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = FacturaService(uow, actor_id=current_user.get("id"))
        return await service.subir_factura(
            usuario_id=current_user.get("id"),
            periodo=periodo,
            detalle=detalle,
            archivo_bytes=content,
            nombre_archivo=archivo.filename or "factura.pdf",
        )


# ── GET /api/docentes/facturas — Own history ────────────────────────────


@router.get(
    "/api/docentes/facturas",
    status_code=HTTP_200_OK,
    response_model=FacturaListResponse,
)
async def get_mis_facturas(
    periodo: Annotated[str | None, Query(min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    _: Annotated[None, Depends(require_permission(PERM_SUBIR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> FacturaListResponse:
    """Get own factura history for the authenticated teacher."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = FacturaService(uow, actor_id=current_user.get("id"))
        return await service.get_historial(
            usuario_id=current_user.get("id"),
            periodo=periodo,
            page=page,
            page_size=page_size,
        )


# ── GET /api/docentes/facturas/{id}/descargar — Download own PDF ─────


@router.get(
    "/api/docentes/facturas/{id}/descargar",
    status_code=HTTP_200_OK,
    response_class=FileResponse,
)
async def descargar_mi_factura(
    id: str,
    _: Annotated[None, Depends(require_permission(PERM_SUBIR))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> FileResponse:
    """Download a PDF file for a factura owned by the authenticated teacher.

    Verifies the factura belongs to the current user before serving.
    Raises 403 if the factura belongs to another user.
    Raises 404 if the factura or file is not found.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = FacturaService(uow, actor_id=current_user.get("id"))
        factura = await service.get_factura(id)

        # Verify ownership — a teacher can only download their own facturas
        if factura.usuario_id != current_user.get("id"):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="You can only download your own facturas",
            )

        file_path = factura.referencia_archivo

        if not os.path.exists(file_path):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="PDF file not found on storage",
            )

        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=os.path.basename(file_path),
        )
