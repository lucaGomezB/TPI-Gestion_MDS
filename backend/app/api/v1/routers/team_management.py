"""Router for team management endpoints — asignaciones, equipo clone, export.

All endpoints are protected:
- Mutating endpoints (POST/PUT) require ``equipo_docente:asignar``
- Read endpoints (GET) require ``equipo_docente:ver``

Endpoints:
- POST/GET/GET{id}/PUT for individual asignaciones
- POST /api/admin/asignaciones/masiva — bulk assignment
- POST /api/admin/asignaciones/clonar — clone equipo
- PUT /api/admin/asignaciones/vigencia — bulk vigencia update
- GET /api/admin/equipos/export — CSV export
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.team_management import (
    AsignacionCreate,
    AsignacionMasivaRequest,
    AsignacionMasivaResponse,
    AsignacionResponse,
    AsignacionUpdate,
    ClonarRequest,
    ClonarResponse,
    VigenciaRequest,
    VigenciaResponse,
)
from app.services.team_management import TeamManagementService

router = APIRouter(tags=["team-management"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


# ── Individual CRUD ────────────────────────────────────────────────────


@router.post(
    "/api/admin/asignaciones",
    status_code=HTTP_201_CREATED,
    response_model=AsignacionResponse,
)
async def create_asignacion(
    body: AsignacionCreate,
    _: Annotated[None, Depends(require_permission("equipo_docente:asignar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsignacionResponse:
    """Create a single assignment."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TeamManagementService(uow)
        return await service.create_asignacion(body)


@router.get(
    "/api/admin/asignaciones",
    response_model=list[AsignacionResponse],
)
async def list_asignaciones(
    _: Annotated[None, Depends(require_permission("equipo_docente:ver"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario_id: Optional[str] = None,
    materia_id: Optional[str] = None,
    carrera_id: Optional[str] = None,
    cohorte_id: Optional[str] = None,
    rol: Optional[str] = None,
    vigente: Optional[bool] = None,
) -> list[AsignacionResponse]:
    """List assignments with optional filters, scoped to tenant."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TeamManagementService(uow)
        return await service.list_asignaciones(
            usuario_id=usuario_id,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            rol=rol,
            vigente=vigente,
        )


@router.get(
    "/api/admin/asignaciones/{id}",
    response_model=AsignacionResponse,
)
async def get_asignacion(
    id: str,
    _: Annotated[None, Depends(require_permission("equipo_docente:ver"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsignacionResponse:
    """Get a single assignment by ID."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TeamManagementService(uow)
        return await service.get_asignacion(id)


@router.put(
    "/api/admin/asignaciones/{id}",
    response_model=AsignacionResponse,
)
async def update_asignacion(
    id: str,
    body: AsignacionUpdate,
    _: Annotated[None, Depends(require_permission("equipo_docente:asignar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsignacionResponse:
    """Partially update an existing assignment."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TeamManagementService(uow)
        return await service.update_asignacion(id, body)


# ── Bulk operations ───────────────────────────────────────────────────


@router.post(
    "/api/admin/asignaciones/masiva",
    status_code=HTTP_201_CREATED,
    response_model=AsignacionMasivaResponse,
)
async def asignacion_masiva(
    body: AsignacionMasivaRequest,
    _: Annotated[None, Depends(require_permission("equipo_docente:asignar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsignacionMasivaResponse:
    """Bulk assign multiple usuarios to the same academic context."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TeamManagementService(uow)
        return await service.asignacion_masiva(body)


@router.post(
    "/api/admin/asignaciones/clonar",
    status_code=HTTP_201_CREATED,
    response_model=ClonarResponse,
)
async def clonar_equipo(
    body: ClonarRequest,
    _: Annotated[None, Depends(require_permission("equipo_docente:asignar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClonarResponse:
    """Clone all Vigente assignments from a source context to a destination."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TeamManagementService(uow)
        return await service.clonar_equipo(body)


@router.put(
    "/api/admin/asignaciones/vigencia",
    response_model=VigenciaResponse,
)
async def actualizar_vigencia(
    body: VigenciaRequest,
    _: Annotated[None, Depends(require_permission("equipo_docente:asignar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VigenciaResponse:
    """Bulk update vigencia dates for all assignments matching filters."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TeamManagementService(uow)
        return await service.actualizar_vigencia(body)


# ── Export ─────────────────────────────────────────────────────────────


@router.get(
    "/api/admin/equipos/export",
)
async def exportar_equipo(
    _: Annotated[None, Depends(require_permission("equipo_docente:ver"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    materia_id: Optional[str] = None,
    carrera_id: Optional[str] = None,
    cohorte_id: Optional[str] = None,
) -> StreamingResponse:
    """Export teaching team as CSV."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TeamManagementService(uow)
        csv_content = await service.exportar_equipo(
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
        )
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=equipo.csv"},
        )
