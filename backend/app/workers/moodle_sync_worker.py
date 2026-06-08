"""Scheduled nocturnal Moodle sync worker.

Runs as an async background task spawned via ``asyncio.create_task``
on FastAPI startup. Waits until the configured sync hour, then
iterates over all tenants with Moodle WS enabled and syncs each
active dictado.

This is an MVP implementation. In production, this should be replaced
with a proper scheduler (APScheduler) or external job.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session_maker
from app.models.tenant import Tenant
from app.services.moodle_config_service import moodle_config_service
from app.services.moodle_sync_service import moodle_sync_service

logger = logging.getLogger(__name__)


async def run_moodle_sync_worker() -> None:
    """Background worker loop for nocturnal Moodle sync.

    Calculates seconds until the next sync hour, sleeps until then,
    then runs sync for all enabled tenants and their active dictados.
    """
    logger.info("Moodle sync worker started")

    while True:
        try:
            _wait_until_sync_hour()

            logger.info("Starting nocturnal Moodle sync cycle")

            session_maker = get_session_maker()
            async with session_maker() as db:
                await _sync_all_tenants(db)

            logger.info("Nocturnal Moodle sync cycle completed")

            # Sleep 24 hours minus small delta to avoid drift
            await asyncio.sleep(23.5 * 3600)

        except asyncio.CancelledError:
            logger.info("Moodle sync worker cancelled")
            break
        except Exception as exc:
            logger.error("Moodle sync worker error: %s", exc, exc_info=True)
            await asyncio.sleep(60)


def _wait_until_sync_hour() -> None:
    """Synchronously calculate and sleep until the next configured sync hour.

    This is a blocking sleep to align with wall-clock time.
    For production, use a proper scheduler instead.
    """
    import time

    settings = get_settings()
    sync_hour = settings.moodle_sync_hour
    now = datetime.now(timezone.utc)
    current_hour = now.hour

    if current_hour < sync_hour:
        # Same day, future hour
        target = now.replace(hour=sync_hour, minute=0, second=0, microsecond=0)
        seconds = (target - now).total_seconds()
    else:
        # Next day
        from datetime import timedelta

        tomorrow = now + timedelta(days=1)
        target = tomorrow.replace(hour=sync_hour, minute=0, second=0, microsecond=0)
        seconds = (target - now).total_seconds()

    if seconds > 0:
        logger.info(
            "Waiting %.1f hours until next sync (hour %d:00 UTC)",
            seconds / 3600,
            sync_hour,
        )
        time.sleep(seconds)


async def _sync_all_tenants(db: AsyncSession) -> None:
    """Iterate over all tenants with Moodle enabled and sync their dictados.

    Per-dictado failures are logged but do not stop processing of
    subsequent dictados or tenants.
    """
    # Get all active tenants
    result = await db.execute(
        select(Tenant).where(Tenant.activo == True, Tenant.config_moodle.isnot(None))  # noqa: E712
    )
    tenants = result.scalars().all()

    for tenant in tenants:
        tenant_id = tenant.id
        try:
            config = await moodle_config_service.get_moodle_config(db, tenant_id)
            if config is None or not config.ws_enabled:
                continue

            # Get active dictados with moodle_course_id
            # In MVP, we use a stub — in C-04, this will query actual dictados
            active_dictados = await _get_active_dictados_for_tenant(db, tenant_id)

            for dictado in active_dictados:
                moodle_course_id = dictado.get("moodle_course_id")
                dictado_id = dictado.get("id")
                if not moodle_course_id or not dictado_id:
                    continue

                try:
                    logger.info(
                        "Nocturnal sync: tenant=%s dictado=%s course=%s",
                        tenant_id,
                        dictado_id,
                        moodle_course_id,
                    )
                    result = await moodle_sync_service.sync_dictado(
                        db=db,
                        tenant_id=tenant_id,
                        dictado_id=dictado_id,
                        moodle_course_id=moodle_course_id,
                        moodle_config=config,
                        sync_type="nocturnal",
                    )
                    logger.info(
                        "Nocturnal sync result for dictado %s: %s",
                        dictado_id,
                        result.status,
                    )
                except Exception as exc:
                    logger.error(
                        "Nocturnal sync failed for dictado %s: %s",
                        dictado_id,
                        exc,
                    )

        except Exception as exc:
            logger.error(
                "Nocturnal sync failed for tenant %s: %s",
                tenant_id,
                exc,
            )


async def _get_active_dictados_for_tenant(
    db: AsyncSession, tenant_id: str
) -> list[dict]:
    """Get active dictados with a moodle_course_id.

    Stub until C-04 (academic core models) is available.
    When C-04 exists, this queries the actual Dictado model.
    """
    # Stub: return empty list until C-04 is implemented
    # In production, this will query:
    #   select(Dictado).where(
    #       Dictado.tenant_id == tenant_id,
    #       Dictado.moodle_course_id.isnot(None),
    #       Dictado.estado != 'Inactivo',
    #   )
    return []
