"""Admin endpoints for per-tenant Moodle configuration management.

- ``GET /api/v1/admin/tenants/moodle-config``: get current Moodle config
- ``PUT /api/v1/admin/tenants/moodle-config``: set/update Moodle config
- ``DELETE /api/v1/admin/tenants/moodle-config``: clear Moodle config
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.moodle_config import MoodleConfigSchema, MoodleConfigUpdateSchema
from app.services.moodle_config_service import moodle_config_service

router = APIRouter(prefix="/api/v1/admin/tenants", tags=["admin-moodle"])


@router.get("/moodle-config")
async def get_moodle_config(
    _: Annotated[None, Depends(require_permission("tenant:configurar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MoodleConfigSchema:
    """Get the current Moodle configuration for the user's tenant.

    Sensitive fields (ws_url, ws_token) are returned decrypted,
    but the ``ws_token`` is partially masked for security.
    """
    tenant_id = current_user["tenant_id"]
    async with UnitOfWork(db, tenant_id) as uow:
        config = await moodle_config_service.get_moodle_config(uow, tenant_id)
    if config is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Moodle configuration not found for this tenant",
        )

    # Mask the token for security
    if config.ws_token:
        config.ws_token = _mask_token(config.ws_token)

    return config


@router.put("/moodle-config")
async def set_moodle_config(
    config_in: MoodleConfigUpdateSchema,
    _: Annotated[None, Depends(require_permission("tenant:configurar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MoodleConfigSchema:
    """Set or update Moodle configuration for the user's tenant.

    Sensitive fields (ws_url, ws_token) are encrypted before storage.
    Returns the decrypted configuration with the token masked.
    """
    tenant_id = current_user["tenant_id"]

    try:
        async with UnitOfWork(db, tenant_id) as uow:
            config = await moodle_config_service.set_moodle_config(
                uow, tenant_id, config_in
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # Mask the token for security
    if config.ws_token:
        config.ws_token = _mask_token(config.ws_token)

    return config


@router.delete("/moodle-config", status_code=204)
async def clear_moodle_config(
    _: Annotated[None, Depends(require_permission("tenant:configurar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Clear the Moodle configuration for the user's tenant."""
    tenant_id = current_user["tenant_id"]

    try:
        async with UnitOfWork(db, tenant_id) as uow:
            await moodle_config_service.clear_moodle_config(uow, tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


def _mask_token(token: str) -> str:
    """Mask all but the last 4 characters of a token."""
    if len(token) <= 4:
        return "****"
    return token[:4] + "****" + token[-4:]
