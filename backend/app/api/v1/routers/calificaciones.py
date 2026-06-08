"""Router for calificaciones (grades) endpoints.

Endpoints:
- POST /api/materias/{materia_id}/calificaciones/importar — import grades
- GET /api/materias/{materia_id}/calificaciones — list grades
- DELETE /api/materias/{materia_id}/calificaciones — clear grades
- POST /api/materias/{materia_id}/calificaciones/umbral — configure threshold
- GET /api/materias/{materia_id}/calificaciones/umbral — get threshold

Permissions:
- ``calificaciones:importar`` for POST (PROFESOR + COORDINADOR + ADMIN)
- ``calificaciones:ver`` for GET list
- ``calificaciones:vaciar`` for DELETE
- ``calificaciones:configurar-umbral`` for POST/GET threshold

Scope (RN-04):
- PROFESOR: only materias where they have an active assignment
- COORDINADOR/ADMIN: any materia in the tenant
"""

import json
import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.models.asignacion import Asignacion
from app.schemas.calificaciones import (
    CalificacionListResponse,
    ImportResultOut,
    PreviewResultOut,
    UmbralMateriaOut,
    UmbralMateriaUpdateIn,
)
from app.services.calificaciones import CalificacionesService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["calificaciones"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


async def _check_materia_access(
    materia_id: str,
    current_user: dict,
    db: AsyncSession,
) -> str | None:
    """Check materia access and return asignacion_id if applicable.

    COORDINADOR and ADMIN roles can access any materia within the tenant.
    PROFESOR must have an active assignment for the materia.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        The asignacion UUID if the user is a PROFESOR with assignment,
        or None if COORDINADOR/ADMIN.

    Raises:
        HTTPException(403): If the user does not have access.
    """
    roles = current_user.get("roles", [])
    user_id = current_user.get("id", "")

    # COORDINADOR and ADMIN have global access within tenant
    if "COORDINADOR" in roles or "ADMIN" in roles:
        return None

    # PROFESOR must have an active assignment for this materia
    today = date.today()
    stmt = (
        select(Asignacion)
        .where(
            Asignacion.tenant_id == _get_tenant_id(current_user),
            Asignacion.usuario_id == user_id,
            Asignacion.materia_id == materia_id,
            Asignacion.vig_desde <= today,
            (
                (Asignacion.vig_hasta >= today)
                | (Asignacion.vig_hasta.is_(None))
            ),
        )
    )
    result = await db.execute(stmt)
    asignacion = result.scalar_one_or_none()
    if asignacion is None:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta materia",
        )
    return asignacion.id


def _is_coordinador(current_user: dict) -> bool:
    """Check if the current user has COORDINADOR or ADMIN role."""
    roles = current_user.get("roles", [])
    return "COORDINADOR" in roles or "ADMIN" in roles


def _get_asignacion_or_none(asignacion_id: str | None) -> str | None:
    """Return asignacion_id or None (handles 'none' sentinel)."""
    if asignacion_id is None or asignacion_id == "none":
        return None
    return asignacion_id


# ── POST /importar (preview + confirm) ─────────────────────────────────────────


@router.post(
    "/api/materias/{materia_id}/calificaciones/importar",
    status_code=HTTP_201_CREATED,
)
async def importar_calificaciones(
    materia_id: str,
    file: Annotated[UploadFile, File(description="CSV or XLSX file")],
    _: Annotated[None, Depends(require_permission("calificaciones:importar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    preview: Annotated[bool, Query(description="Preview mode — no persist")] = False,
    actividades_seleccionadas: Annotated[
        str | None,
        Form(description="JSON array of activity names (required in confirm mode)"),
    ] = None,
) -> PreviewResultOut | ImportResultOut:
    """Import grades from CSV or XLSX file.

    Two modes via ``?preview`` query param:

    1. **Preview** (``?preview=true``):
       Parse file, detect activities, return metadata without persisting.

    2. **Confirm** (``?preview=false`` or omitted):
       Parse file, filter by ``actividades_seleccionadas``, persist atomically.
       In confirm mode, send ``actividades_seleccionadas`` as a multipart form
       field containing a JSON array string, e.g. ``["TP 1", "TP 2"]``.

    Args:
        materia_id: The materia UUID.
        file: The uploaded CSV or XLSX file.
        current_user: Authenticated user from JWT.
        db: Database session.
        preview: If True, run in preview mode (no persist).
        actividades_seleccionadas: JSON array of activity names for confirm mode.

    Returns:
        ``PreviewResultOut`` in preview mode, ``ImportResultOut`` otherwise.
    """
    asignacion_id = await _check_materia_access(materia_id, current_user, db)

    file_bytes = await file.read()
    filename = file.filename or "upload.csv"

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CalificacionesService(uow)

        if preview:
            return await service.preview_import(
                materia_id=materia_id,
                file_bytes=file_bytes,
                filename=filename,
            )

        # Confirm mode
        if not actividades_seleccionadas:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=(
                    "Debe proporcionar actividades_seleccionadas "
                    "(JSON array) en modo confirmacion"
                ),
            )

        try:
            actividades_list: list[str] = json.loads(actividades_seleccionadas)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="actividades_seleccionadas debe ser un array JSON de strings",
            )

        if not actividades_list:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Debe seleccionar al menos una actividad",
            )

        return await service.confirm_import(
            materia_id=materia_id,
            file_bytes=file_bytes,
            filename=filename,
            actividades_seleccionadas=actividades_list,
            usuario_id=current_user.get("id", ""),
            asignacion_id=_get_asignacion_or_none(asignacion_id),
        )


# ── GET / (list) ──────────────────────────────────────────────────────────────


@router.get(
    "/api/materias/{materia_id}/calificaciones",
    response_model=CalificacionListResponse,
)
async def listar_calificaciones(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("calificaciones:ver"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    actividad: Annotated[
        str | None, Query(description="Filter by activity name")
    ] = None,
    aprobado: Annotated[
        bool | None, Query(description="Filter by approval status")
    ] = None,
) -> CalificacionListResponse:
    """List grade records for a materia.

    Supports optional filters by activity name and approval status.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.
        actividad: Optional activity name filter.
        aprobado: Optional approval status filter.

    Returns:
        A ``CalificacionListResponse`` with items and total count.
    """
    await _check_materia_access(materia_id, current_user, db)

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CalificacionesService(uow)
        return await service.list_calificaciones(
            materia_id=materia_id,
            actividad=actividad,
            aprobado=aprobado,
        )


# ── DELETE / (scope-isolated) ─────────────────────────────────────────────────


@router.delete(
    "/api/materias/{materia_id}/calificaciones",
    status_code=HTTP_200_OK,
)
async def vaciar_calificaciones(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("calificaciones:vaciar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    confirmar: Annotated[
        bool, Query(description="Must be true to execute deletion")
    ] = False,
) -> dict:
    """Delete grade records with scope isolation (RN-04).

    - PROFESOR: deletes only records where ``cargado_por`` matches.
    - COORDINADOR/ADMIN: deletes ALL records for the materia.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.
        confirmar: Must be ``true`` to execute deletion.

    Returns:
        A dict with ``eliminados`` count.

    Raises:
        HTTPException(400): If ``confirmar`` is not ``true``.
    """
    if not confirmar:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Debe confirmar la operacion con ?confirmar=true",
        )

    await _check_materia_access(materia_id, current_user, db)

    es_coordinador = _is_coordinador(current_user)
    usuario_id = current_user.get("id", "")

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CalificacionesService(uow)
        eliminados = await service.clear_calificaciones(
            materia_id=materia_id,
            usuario_id=usuario_id,
            es_coordinador=es_coordinador,
        )

        return {"eliminados": eliminados}


# ── POST /umbral ──────────────────────────────────────────────────────────────


@router.post(
    "/api/materias/{materia_id}/calificaciones/umbral",
    response_model=UmbralMateriaOut,
)
async def configurar_umbral(
    materia_id: str,
    data: UmbralMateriaUpdateIn,
    _: Annotated[None, Depends(require_permission("calificaciones:configurar-umbral"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UmbralMateriaOut:
    """Create or update approval threshold for this materia.

    Args:
        materia_id: The materia UUID.
        data: Threshold configuration body.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        The ``UmbralMateriaOut`` with saved values.
    """
    asignacion_id = await _check_materia_access(materia_id, current_user, db)
    if asignacion_id is None:
        # COORDINADOR/ADMIN — use first active asignacion for this materia
        today = date.today()
        stmt = (
            select(Asignacion)
            .where(
                Asignacion.tenant_id == _get_tenant_id(current_user),
                Asignacion.materia_id == materia_id,
                Asignacion.vig_desde <= today,
                (
                    (Asignacion.vig_hasta >= today)
                    | (Asignacion.vig_hasta.is_(None))
                ),
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        first_asignacion = result.scalar_one_or_none()
        if first_asignacion is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="No se encontro una asignacion activa para esta materia",
            )
        asignacion_id = first_asignacion.id

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CalificacionesService(uow)
        return await service.set_threshold(
            materia_id=materia_id,
            asignacion_id=asignacion_id,
            data=data.model_dump(exclude_unset=True),
        )


# ── GET /umbral ───────────────────────────────────────────────────────────────


@router.get(
    "/api/materias/{materia_id}/calificaciones/umbral",
    response_model=UmbralMateriaOut,
)
async def obtener_umbral(
    materia_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(require_permission("calificaciones:configurar-umbral"))],
) -> UmbralMateriaOut:
    """Get current approval threshold (or defaults if not configured).

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        The ``UmbralMateriaOut`` with current or default threshold values.
    """
    asignacion_id = await _check_materia_access(materia_id, current_user, db)
    if asignacion_id is None:
        # COORDINADOR/ADMIN — use first active asignacion
        today = date.today()
        stmt = (
            select(Asignacion)
            .where(
                Asignacion.tenant_id == _get_tenant_id(current_user),
                Asignacion.materia_id == materia_id,
                Asignacion.vig_desde <= today,
                (
                    (Asignacion.vig_hasta >= today)
                    | (Asignacion.vig_hasta.is_(None))
                ),
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        first_asignacion = result.scalar_one_or_none()
        if first_asignacion:
            asignacion_id = first_asignacion.id

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CalificacionesService(uow)
        return await service.get_threshold(
            materia_id=materia_id,
            asignacion_id=asignacion_id or "none",
        )
