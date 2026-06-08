"""Router for tareas internas endpoints (C-16).

Endpoints:
- GET /api/tareas — list my assigned tasks (F8.1)
- POST /api/tareas — assign a task (F8.2)
- PUT /api/tareas/{id}/estado — change task estado
- POST /api/tareas/{id}/comentarios — add comment
- GET /api/admin/tareas — admin global view with filters (F8.3)

Permission guards:
- ``tareas:ver`` for GET /api/tareas
- ``tareas:asignar`` for POST /api/tareas
- ``tareas:admin`` for GET /api/admin/tareas
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.tarea import (
    ComentarioCreate,
    ComentarioRead,
    TareaCreate,
    TareaEstadoUpdate,
    TareaFilter,
    TareaRead,
    TareaReadAdmin,
)
from app.services.tareas import TareaService

router = APIRouter(tags=["tareas"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


# ── F8.1: GET /api/tareas — Mis tareas asignadas ────────────────────────


@router.get(
    "/api/tareas",
    response_model=list[TareaRead],
    status_code=HTTP_200_OK,
)
async def list_mis_tareas(
    estado: Annotated[str | None, Query(description="Filter by estado")] = None,
    materia_id: Annotated[str | None, Query(description="Filter by materia UUID")] = None,
    _: Annotated[None, Depends(require_permission("tareas:ver"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[TareaRead]:
    """List tasks assigned to the authenticated user (F8.1).

    Supports optional filters by ``estado`` and ``materia_id``.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TareaService(uow, current_user)
        filters = TareaFilter(estado=estado, materia_id=materia_id)
        tareas = await service.get_mis_tareas(filters)
        return [TareaRead.model_validate(t) for t in tareas]


# ── F8.2: POST /api/tareas — Asignar tarea ──────────────────────────────


@router.post(
    "/api/tareas",
    response_model=TareaRead,
    status_code=HTTP_201_CREATED,
)
async def create_tarea(
    body: TareaCreate,
    _: Annotated[None, Depends(require_permission("tareas:asignar"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> TareaRead:
    """Assign a new task to a user (F8.2).

    Creates a task with ``asignado_por`` set to the authenticated user.
    ``materia_id`` is optional — if omitted, the task is institutional.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TareaService(uow, current_user)
        tarea = await service.create_tarea(body)
        return TareaRead.model_validate(tarea)


# ── PUT /api/tareas/{id}/estado — Cambiar estado ────────────────────────


@router.put(
    "/api/tareas/{id}/estado",
    response_model=TareaRead,
    status_code=HTTP_200_OK,
)
async def change_tarea_estado(
    id: str,
    body: TareaEstadoUpdate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> TareaRead:
    """Change the estado of a task.

    Enforces forward-only flow: Pendiente -> En progreso -> Resuelta.
    Cancelada is allowed from any state.
    Only the assigned user or users with ``tareas:admin`` can change estado.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TareaService(uow, current_user)
        tarea = await service.change_estado(id, body)
        return TareaRead.model_validate(tarea)


# ── POST /api/tareas/{id}/comentarios — Agregar comentario ──────────────


@router.post(
    "/api/tareas/{id}/comentarios",
    response_model=ComentarioRead,
    status_code=HTTP_201_CREATED,
)
async def add_comentario(
    id: str,
    body: ComentarioCreate,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ComentarioRead:
    """Add an immutable comment to a task.

    Comments are append-only: once created, they cannot be edited or deleted.
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TareaService(uow, current_user)
        comentario = await service.add_comentario(id, body)
        return ComentarioRead.model_validate(comentario)


# ── F8.3: GET /api/admin/tareas — Vista global admin ─────────────────────


@router.get(
    "/api/admin/tareas",
    response_model=list[TareaReadAdmin],
    status_code=HTTP_200_OK,
)
async def list_admin_tareas(
    estado: Annotated[str | None, Query(description="Filter by estado")] = None,
    materia_id: Annotated[str | None, Query(description="Filter by materia UUID")] = None,
    asignado_a: Annotated[str | None, Query(description="Filter by assigned user UUID")] = None,
    asignado_por: Annotated[str | None, Query(description="Filter by assigner user UUID")] = None,
    q: Annotated[str | None, Query(description="Free-text search in descripcion")] = None,
    _: Annotated[None, Depends(require_permission("tareas:admin"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[TareaReadAdmin]:
    """View all tasks across the tenant with filters (F8.3).

    Filters are conjunctive: all provided filters must match.
    Available filters: ``estado``, ``materia_id``, ``asignado_a``,
    ``asignado_por``, and ``q`` (free-text search in descripcion).
    """
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = TareaService(uow, current_user)
        filters = TareaFilter(
            estado=estado,
            materia_id=materia_id,
            asignado_a=asignado_a,
            asignado_por=asignado_por,
            q=q,
        )
        tareas = await service.get_admin_tareas(filters)
        return [TareaReadAdmin(**t) for t in tareas]
