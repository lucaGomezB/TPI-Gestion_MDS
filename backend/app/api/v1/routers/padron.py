"""Router for padron de alumnos (student roster) endpoints.

Endpoints:
- POST /api/materias/{materia_id}/padron/importar — import CSV/XLSX roster
- GET /api/materias/{materia_id}/padron — list active entries
- GET /api/materias/{materia_id}/padron/versiones — version history

Permissions:
- ``padron:importar`` for POST (PROFESOR + COORDINADOR + ADMIN)
- ``padron:ver`` for GETs (PROFESOR + COORDINADOR + ADMIN)

Scoping (D5):
- PROFESOR: only materias where they have an active assignment
- COORDINADOR: any materia in the tenant
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.models.asignacion import Asignacion
from app.schemas.padron import (
    EntradaPadronOut,
    ImportResultOut,
    VersionHistoryOut,
)
from app.services.padron import PadronService

router = APIRouter(tags=["padron"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


async def _check_materia_access(
    materia_id: str,
    current_user: dict,
    db: AsyncSession,
) -> None:
    """Check that a PROFESOR has an active assignment for the materia.

    COORDINADOR and ADMIN roles can access any materia within the tenant.
    """
    roles = current_user.get("roles", [])
    # COORDINADOR and ADMIN have global access within tenant
    if "COORDINADOR" in roles or "ADMIN" in roles:
        return

    # PROFESOR must have an active assignment for this materia
    user_id = current_user.get("id", "")
    from datetime import date

    today = date.today()
    stmt = (
        select(Asignacion)
        .where(
            Asignacion.tenant_id == _get_tenant_id(current_user),
            Asignacion.usuario_id == user_id,
            Asignacion.materia_id == materia_id,
            Asignacion.vig_desde <= today,
            (
                (Asignacion.vig_hasta >= today) | (Asignacion.vig_hasta.is_(None))
            ),
        )
    )
    result = await db.execute(stmt)
    asignacion = result.scalar_one_or_none()
    if asignacion is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta materia",
        )


@router.post(
    "/api/materias/{materia_id}/padron/importar",
    status_code=HTTP_201_CREATED,
    response_model=ImportResultOut,
)
async def importar_padron(
    materia_id: str,
    file: Annotated[UploadFile, File(...)],
    cohorte_id: str,
    _: Annotated[None, Depends(require_permission("padron:importar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImportResultOut:
    """Import a student roster from CSV or XLSX file.

    Creates a new version, deactivates the previous one, and bulk-inserts
    entries in an atomic transaction.

    Args:
        materia_id: The materia UUID path parameter.
        file: The uploaded CSV or XLSX file.
        cohorte_id: Query parameter with the cohorte UUID.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        ``ImportResultOut`` with version_id and total_imported count.
    """
    await _check_materia_access(materia_id, current_user, db)

    file_bytes = await file.read()
    filename = file.filename or "upload.csv"

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = PadronService(uow)
        return await service.import_roster(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            file_bytes=file_bytes,
            filename=filename,
            usuario_id=current_user.get("id", ""),
        )


@router.get(
    "/api/materias/{materia_id}/padron",
    response_model=list[EntradaPadronOut],
)
async def listar_padron(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("padron:ver"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[EntradaPadronOut]:
    """List active padron entries for a materia.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        A list of ``EntradaPadronOut`` instances.
    """
    await _check_materia_access(materia_id, current_user, db)

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = PadronService(uow)
        return await service.get_active_entries(materia_id)


@router.get(
    "/api/materias/{materia_id}/padron/versiones",
    response_model=list[VersionHistoryOut],
)
async def listar_versiones(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("padron:ver"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[VersionHistoryOut]:
    """List version history for a materia's padron.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        A list of ``VersionHistoryOut`` instances.
    """
    await _check_materia_access(materia_id, current_user, db)

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = PadronService(uow)
        return await service.get_version_history(materia_id)
