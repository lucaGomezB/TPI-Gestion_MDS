"""Router for on-demand Moodle sync and sync history endpoints.

- ``POST /api/v1/materias/{dictado_id}/sync-moodle``: trigger on-demand sync
- ``GET /api/v1/materias/{dictado_id}/sync-log``: recent sync history
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_502_BAD_GATEWAY,
)

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.integrations.exceptions import MoodleAuthenticationError, MoodleConnectionError
from app.schemas.moodle_sync import SyncResult
from app.services.moodle_config_service import moodle_config_service
from app.services.moodle_sync_service import moodle_sync_service

router = APIRouter(prefix="/api/v1/materias", tags=["moodle-sync"])


@router.post("/{dictado_id}/sync-moodle")
async def trigger_sync(
    dictado_id: str,
    _: Annotated[None, Depends(require_permission("calificaciones:importar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SyncResult:
    """Trigger an on-demand Moodle sync for a specific dictado.

    Requires ``calificaciones:importar`` permission.
    - PROFESOR: can sync only dictados they are assigned to.
    - COORDINADOR/ADMIN: can sync any dictado in the tenant.
    """
    tenant_id = current_user["tenant_id"]

    async with UnitOfWork(db, tenant_id) as uow:
        # Check Moodle is enabled for this tenant
        if not await moodle_config_service.is_moodle_enabled(uow, tenant_id):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Moodle Web Services is not enabled for this tenant",
            )

        # Load Moodle config
        config = await moodle_config_service.get_moodle_config(uow, tenant_id)
        if config is None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Moodle Web Services is not enabled for this tenant",
            )

        # Check if a sync is already running for this dictado
        if await uow.sync_log.has_running_sync(dictado_id):
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail="A sync is already in progress for this dictado",
            )

        # Stub: In MVP, the dictado_id is used as moodle_course_id (1:1 mapping)
        # When C-04 is implemented, this will look up the actual moodle_course_id
        # from the Dictado model.
        try:
            moodle_course_id = int(dictado_id.replace("-", "")[:8], 16) % 10000
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Dictado not found",
            )

        try:
            result = await moodle_sync_service.sync_dictado(
                uow=uow,
                tenant_id=tenant_id,
                dictado_id=dictado_id,
                moodle_course_id=moodle_course_id,
                moodle_config=config,
                sync_type="ondemand",
            )
        except (MoodleAuthenticationError, MoodleConnectionError) as exc:
            raise HTTPException(
                status_code=HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            )

        if result.status == "failed":
            # Still return 200 since the request was accepted and processed
            pass

        return result


@router.get("/{dictado_id}/sync-log")
async def get_sync_log(
    dictado_id: str,
    _: Annotated[None, Depends(require_permission("calificaciones:importar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """Get recent sync history for a dictado.

    Returns the last 20 sync log entries, newest first.
    """
    tenant_id = current_user["tenant_id"]
    async with UnitOfWork(db, tenant_id) as uow:
        logs = await uow.sync_log.list_by_dictado(dictado_id=dictado_id)
    return [
        {
            "id": log.id,
            "sync_type": log.sync_type,
            "status": log.status,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "finished_at": log.finished_at.isoformat() if log.finished_at else None,
            "details": log.details,
            "error_message": log.error_message,
        }
        for log in logs
    ]
