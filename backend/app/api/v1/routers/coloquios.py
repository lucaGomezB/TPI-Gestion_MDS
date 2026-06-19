"""Router for coloquio management endpoints.

Endpoints:
- POST /api/materias/{materia_id}/coloquios — crear convocatoria (F7.3)
- GET /api/materias/{materia_id}/coloquios — listar convocatorias activas
- POST /api/materias/{materia_id}/coloquios/importar-alumnos — importar padron
- POST /api/coloquios/{evaluacion_id}/reservar — reserva de alumno
- GET /api/coloquios/{evaluacion_id}/agenda — agenda consolidada
- POST /api/coloquios/{evaluacion_id}/resultados — registrar resultados
- GET /api/admin/coloquios/metricas — panel de metricas
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.coloquios import (
    AgendaColoquioResponse,
    ColoquioListResponse,
    EvaluacionColoquioCreate,
    EvaluacionColoquioResponse,
    ImportarAlumnosRequest,
    ImportarAlumnosResponse,
    MetricasColoquioResponse,
    ReservaColoquioCreate,
    ReservaColoquioResponse,
    ResultadoColoquioCreate,
    ResultadoColoquioResponse,
)
from app.services.coloquios import ColoquioService

# ── Routers ───────────────────────────────────────────────────────────────────

router_materias = APIRouter(tags=["coloquios"])
router_coloquios = APIRouter(tags=["coloquios"])
router_admin = APIRouter(tags=["coloquios"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


# ── POST /api/materias/{materia_id}/coloquios — Crear convocatoria ───────────


@router_materias.post(
    "/api/materias/{materia_id}/coloquios",
    status_code=HTTP_201_CREATED,
    response_model=EvaluacionColoquioResponse,
)
async def crear_convocatoria(
    materia_id: str,
    body: EvaluacionColoquioCreate,
    _: Annotated[None, Depends(require_permission("coloquios:crear"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EvaluacionColoquioResponse:
    """Create a new coloquio convocatoria (F7.3)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ColoquioService(uow, current_user)
        return await service.crear_convocatoria(materia_id, body)


# ── GET /api/materias/{materia_id}/coloquios — Listar convocatorias ──────────


@router_materias.get(
    "/api/materias/{materia_id}/coloquios",
    status_code=HTTP_200_OK,
    response_model=ColoquioListResponse,
)
async def listar_convocatorias(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("coloquios:crear"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ColoquioListResponse:
    """List active coloquio convocatorias for a materia."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ColoquioService(uow, current_user)
        items = await service.listar_convocatorias(materia_id)
        return ColoquioListResponse(items=items, total=len(items))


# ── POST /api/materias/{materia_id}/coloquios/importar-alumnos ───────────────


@router_materias.post(
    "/api/materias/{materia_id}/coloquios/importar-alumnos",
    status_code=HTTP_200_OK,
    response_model=ImportarAlumnosResponse,
)
async def importar_alumnos(
    materia_id: str,
    body: ImportarAlumnosRequest,
    _: Annotated[None, Depends(require_permission("coloquios:importar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImportarAlumnosResponse:
    """Import students into a coloquio from materia padron."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ColoquioService(uow, current_user)
        return await service.importar_alumnos(materia_id, body)


# ── GET /api/coloquios — Global listing ──────────────────────────────────────


@router_coloquios.get(
    "/api/coloquios",
    status_code=HTTP_200_OK,
)
async def list_coloquios_global(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """List all active coloquios scoped to the current tenant.

    Accessible by any authenticated user with coloquios visibility.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        # Use base list() which includes tenant scope via _stmt()
        coloquios = await uow.evaluacion_coloquio.list_activas()
        return [
            {
                "id": c.id,
                "materia_id": c.materia_id,
                "nombre": c.nombre,
                "fecha_inicio": c.fecha_inicio.isoformat() if c.fecha_inicio else None,
                "fecha_fin": c.fecha_fin.isoformat() if c.fecha_fin else None,
                "cupo": c.cupo,
                "tenant_id": c.tenant_id,
            }
            for c in coloquios
        ]


# ── POST /api/coloquios/{evaluacion_id}/reservar — Reservar turno ────────────


@router_coloquios.post(
    "/api/coloquios/{evaluacion_id}/reservar",
    status_code=HTTP_201_CREATED,
    response_model=ReservaColoquioResponse,
)
async def reservar_turno(
    evaluacion_id: str,
    body: ReservaColoquioCreate,
    _: Annotated[None, Depends(require_permission("coloquios:reservar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReservaColoquioResponse:
    """Reserve a coloquio turn for the authenticated student."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ColoquioService(uow, current_user)
        return await service.reservar_turno(evaluacion_id, body)


# ── GET /api/coloquios/{evaluacion_id}/agenda — Agenda consolidada ───────────


@router_coloquios.get(
    "/api/coloquios/{evaluacion_id}/agenda",
    status_code=HTTP_200_OK,
    response_model=AgendaColoquioResponse,
)
async def obtener_agenda(
    evaluacion_id: str,
    _: Annotated[None, Depends(require_permission("coloquios:ver_agenda"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgendaColoquioResponse:
    """Get consolidated agenda with reservations per day."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ColoquioService(uow, current_user)
        return await service.obtener_agenda(evaluacion_id)


# ── POST /api/coloquios/{evaluacion_id}/resultados — Registrar resultado ─────


@router_coloquios.post(
    "/api/coloquios/{evaluacion_id}/resultados",
    status_code=HTTP_201_CREATED,
    response_model=ResultadoColoquioResponse,
)
async def registrar_resultado(
    evaluacion_id: str,
    body: ResultadoColoquioCreate,
    _: Annotated[None, Depends(require_permission("coloquios:resultados"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResultadoColoquioResponse:
    """Register a student's coloquio result."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ColoquioService(uow, current_user)
        return await service.registrar_resultado(evaluacion_id, body)


# ── GET /api/admin/coloquios/metricas — Metricas admin ────────────────────────


@router_admin.get(
    "/api/admin/coloquios/metricas",
    status_code=HTTP_200_OK,
    response_model=MetricasColoquioResponse,
)
async def obtener_metricas(
    _: Annotated[None, Depends(require_permission("coloquios:metricas"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MetricasColoquioResponse:
    """Get coloquio admin metrics."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ColoquioService(uow, current_user)
        return await service.obtener_metricas()
