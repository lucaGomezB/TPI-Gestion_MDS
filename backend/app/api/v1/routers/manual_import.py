"""Router for manual grade import (xlsx/csv) endpoints.

- ``POST /api/v1/materias/{dictado_id}/import/preview``: upload file, get preview
- ``POST /api/v1/materias/{dictado_id}/import/confirm``: confirm and persist import
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.manual_import import (
    ImportConfirmRequest,
    ImportResult,
    PreviewResult,
)
from app.services.manual_import_service import manual_import_service

router = APIRouter(prefix="/api/v1/materias", tags=["manual-import"])

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/{dictado_id}/import/preview")
async def upload_preview(
    dictado_id: str,
    file: UploadFile,
    _: Annotated[None, Depends(require_permission("calificaciones:importar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> PreviewResult:
    """Upload a grade file for preview before import.

    Accepts ``.xlsx`` or ``.csv`` files. Returns detected activities,
    student count, and any warnings.

    Requires ``calificaciones:importar`` permission.
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("xlsx", "csv"):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Supported formats: .xlsx, .csv",
        )

    # Read file content
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"File too large (max {_MAX_FILE_SIZE // (1024 * 1024)} MB)",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    try:
        preview = await manual_import_service.parse_and_preview(
            filename=file.filename,
            file_content=content,
            dictado_id=dictado_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return preview


@router.post("/{dictado_id}/import/confirm")
async def confirm_import(
    dictado_id: str,
    request: ImportConfirmRequest,
    _: Annotated[None, Depends(require_permission("calificaciones:importar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImportResult:
    """Confirm and persist an import from a preview session.

    Requires ``calificaciones:importar`` permission.
    """
    tenant_id = current_user["tenant_id"]

    try:
        async with UnitOfWork(db, tenant_id) as uow:
            result = await manual_import_service.confirm_import(
                request=request,
                db=uow,
                tenant_id=tenant_id,
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return result
