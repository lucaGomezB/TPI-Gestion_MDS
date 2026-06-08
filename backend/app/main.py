"""FastAPI application entry point.

Creates the ASGI app, registers lifespan handlers (DB init/teardown),
exception handlers, and mounts all API routers.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routers import (
    academic_structure_router,
    admin_facturas_router,
    admin_auditoria_router,
    admin_moodle_router,
    admin_reportes_router,
    atrasados_ranking_router,
    auth_router,
    avisos_admin_router,
    avisos_publico_router,
    calificaciones_router,
    coloquios_admin_router,
    coloquios_materias_router,
    coloquios_router,
    communication_router,
    docente_facturas_router,
    encuentros_router,
    grilla_salarial_router,
    guardias_router,
    health_router,
    liquidaciones_router,
    manual_import_router,
    mensajeria_router,
    moodle_sync_router,
    padron_router,
    reportes_router,
    tareas_router,
    team_management_router,
)
from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import JSONFormatter

APP_VERSION = "0.1.0"


def _configure_logging() -> None:
    """Set up structured JSON logging on the root logger."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan: initialize DB on startup, close on shutdown."""
    _configure_logging()
    init_db()

    # Start nocturnal Moodle sync worker
    sync_task: asyncio.Task[None] | None = None
    if get_settings().environment != "test":
        from app.workers.moodle_sync_worker import run_moodle_sync_worker

        sync_task = asyncio.create_task(run_moodle_sync_worker())
        logging.getLogger(__name__).info("Moodle sync worker started")

    yield

    # Cancel worker on shutdown
    if sync_task is not None:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass

    await close_db()


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    app = FastAPI(
        title="activia-trace",
        version=APP_VERSION,
        lifespan=lifespan,
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Mount routers
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(admin_facturas_router)
    app.include_router(avisos_admin_router)
    app.include_router(avisos_publico_router)
    app.include_router(academic_structure_router)
    app.include_router(docente_facturas_router)
    app.include_router(moodle_sync_router)
    app.include_router(admin_auditoria_router)
    app.include_router(admin_moodle_router)
    app.include_router(admin_reportes_router)
    app.include_router(team_management_router)
    app.include_router(manual_import_router)
    app.include_router(padron_router)
    app.include_router(communication_router)
    app.include_router(encuentros_router)
    app.include_router(calificaciones_router)
    app.include_router(coloquios_materias_router)
    app.include_router(coloquios_router)
    app.include_router(coloquios_admin_router)
    app.include_router(grilla_salarial_router)
    app.include_router(guardias_router)
    app.include_router(liquidaciones_router)
    app.include_router(mensajeria_router)
    app.include_router(tareas_router)
    app.include_router(atrasados_ranking_router)
    app.include_router(reportes_router)

    return app


app = create_app()
