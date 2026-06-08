"""Router for encuentro management endpoints.

Endpoints:
- POST /api/materias/{id}/encuentros/slot — crear slot recurrente (F6.1)
- POST /api/materias/{id}/encuentros/unico — crear encuentro unico (F6.2)
- PUT /api/encuentros/{id} — editar instancia individual (F6.3, RN-14)
- POST /api/materias/{id}/encuentros/embed — generar snippet HTML/Markdown (F6.4)
- GET /api/admin/encuentros — vista transversal (F6.5)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.encuentros import (
    EmbedResponse,
    InstanciaEncuentroCreate,
    InstanciaEncuentroResponse,
    InstanciaEncuentroUpdate,
    SlotEncuentroCreate,
    SlotEncuentroResponse,
)
from app.services.encuentros import EncuentroService

router = APIRouter(tags=["encuentros"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


# ── Slot recurrente ──────────────────────────────────────────────────────────


@router.post(
    "/api/materias/{materia_id}/encuentros/slot",
    status_code=HTTP_201_CREATED,
)
async def crear_slot_recurrente(
    materia_id: str,
    body: SlotEncuentroCreate,
    _: Annotated[None, Depends(require_permission("encuentros:crear"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Create a recurrent slot with eager instance generation (F6.1)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = EncuentroService(uow)
        slot, instancias = await service.crear_slot_recurrente(body)
        return {
            "slot": slot.model_dump(),
            "instancias": [i.model_dump() for i in instancias],
            "total_instancias": len(instancias),
        }


# ── Encuentro unico ──────────────────────────────────────────────────────────


@router.post(
    "/api/materias/{materia_id}/encuentros/unico",
    status_code=HTTP_201_CREATED,
    response_model=InstanciaEncuentroResponse,
)
async def crear_encuentro_unico(
    materia_id: str,
    body: InstanciaEncuentroCreate,
    _: Annotated[None, Depends(require_permission("encuentros:crear"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InstanciaEncuentroResponse:
    """Create a single encuentro without a slot (F6.2)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = EncuentroService(uow)
        return await service.crear_encuentro_unico(body)


# ── Editar instancia ─────────────────────────────────────────────────────────


@router.put(
    "/api/encuentros/{id}",
    status_code=HTTP_200_OK,
    response_model=InstanciaEncuentroResponse,
)
async def editar_instancia(
    id: str,
    body: InstanciaEncuentroUpdate,
    _: Annotated[None, Depends(require_permission("encuentros:editar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InstanciaEncuentroResponse:
    """Edit an individual encounter instance (F6.3, RN-14)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = EncuentroService(uow)
        return await service.editar_instancia(id, body)


# ── Embed snippet ────────────────────────────────────────────────────────────


@router.post(
    "/api/materias/{materia_id}/encuentros/embed",
    status_code=HTTP_200_OK,
    response_model=EmbedResponse,
)
async def generar_embed(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("encuentros:ver_todas"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    estado: str | None = Query(None),
    limit: int = Query(default=20, ge=1, le=100),
) -> EmbedResponse:
    """Generate HTML and Markdown snippet for Moodle embedding (F6.4)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = EncuentroService(uow)
        return await service.generar_embed(
            materia_id=materia_id,
            estado=estado,
            limit=limit,
        )


# ── Vista transversal ────────────────────────────────────────────────────────


@router.get(
    "/api/admin/encuentros",
    status_code=HTTP_200_OK,
)
async def vista_transversal_encuentros(
    _: Annotated[None, Depends(require_permission("encuentros:ver_todas"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    materia_id: str | None = Query(None),
    estado: str | None = Query(None),
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
) -> dict:
    """Vista transversal de todos los encuentros del tenant (F6.5).

    COORDINADOR and ADMIN can see all encuentros across materias.
    """
    from datetime import date

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        repo = uow.instancia_encuentro

        if materia_id:
            instances = await repo.list_by_materia(
                materia_id=materia_id,
                estado=estado,
                fecha_desde=date.fromisoformat(fecha_desde) if fecha_desde else None,
                fecha_hasta=date.fromisoformat(fecha_hasta) if fecha_hasta else None,
            )
        else:
            instances = await repo.list()

        # Filter by estado after listing if no materia filter
        if estado is not None and materia_id is None:
            instances = [i for i in instances if i.estado == estado]

        return {
            "total": len(instances),
            "instancias": [
                InstanciaEncuentroResponse.model_validate(i).model_dump()
                for i in instances
            ],
        }
