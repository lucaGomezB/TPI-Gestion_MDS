"""Router for user-facing materia endpoints.

Endpoints:
- GET /api/materias — list materias for the current user (from asignaciones)
- GET /api/materias/{materia_id} — single materia detail for the current user

These endpoints derive the materia list from the user's Asignacion records,
not from the admin catalog. Each materia may appear multiple times if the
user is assigned to different cohorts/comisiones for the same materia.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from app.core.dependencies import get_current_user, get_db
from app.core.unit_of_work import UnitOfWork
from app.schemas.mis_materias import MateriaResponse
from app.repositories.academic_structure import MateriaRepository
from app.repositories.team_management import AsignacionRepository

router = APIRouter(tags=["mis-materias"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


@router.get(
    "/api/materias",
    status_code=HTTP_200_OK,
    response_model=list[MateriaResponse],
)
async def list_mis_materias(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MateriaResponse]:
    """List materias for the current user based on their vigente asignaciones.

    Each asignacion links to a materia + cohorte + comisiones.  The endpoint
    groups by materia_id and aggregates comisiones from all asignaciones.
    """
    tenant_id = _get_tenant_id(current_user)
    usuario_id = current_user["id"]

    async with UnitOfWork(db, tenant_id) as uow:
        asignaciones = await uow.asignacion.list_by_filters(
            usuario_id=usuario_id,
            vigente=True,
        )

        if not asignaciones:
            return []

        # Collect unique materia_ids and cohorte_ids
        materia_ids: set[str] = set()
        cohorte_ids: set[str] = set()
        for a in asignaciones:
            if a.materia_id:
                materia_ids.add(a.materia_id)
            if a.cohorte_id:
                cohorte_ids.add(a.cohorte_id)

        if not materia_ids:
            return []

        # Fetch materias and cohortes
        materia_repo = MateriaRepository(db, tenant_id)
        cohorte_repo = uow.cohorte

        materias_map: dict[str, str] = {}  # id -> nombre
        for mid in materia_ids:
            m = await materia_repo.get_by_id(mid)
            if m is not None:
                materias_map[m.id] = m.nombre

        cohortes_map: dict[str, str] = {}  # id -> nombre
        for cid in cohorte_ids:
            c = await cohorte_repo.get_by_id(cid)
            if c is not None:
                cohortes_map[c.id] = str(c.nombre)

        # Build response: group by materia_id, collect comisiones and cohortes
        grouped: dict[str, dict] = {}
        for a in asignaciones:
            if not a.materia_id or a.materia_id not in materias_map:
                continue
            mid = a.materia_id
            if mid not in grouped:
                grouped[mid] = {
                    "id": mid,
                    "nombre": materias_map[mid],
                    "cohorte": cohortes_map.get(a.cohorte_id, "") if a.cohorte_id else "",
                    "comisiones": set(),
                    "tenant_id": tenant_id,
                }
            grouped[mid]["comisiones"].update(a.comisiones)

        return [
            MateriaResponse(**{**v, "comisiones": sorted(v["comisiones"])})
            for v in grouped.values()
        ]


@router.get(
    "/api/materias/{materia_id}",
    status_code=HTTP_200_OK,
    response_model=MateriaResponse,
)
async def get_mis_materia(
    materia_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MateriaResponse:
    """Get a single materia detail for the current user's asignaciones."""
    tenant_id = _get_tenant_id(current_user)
    usuario_id = current_user["id"]

    async with UnitOfWork(db, tenant_id) as uow:
        # Check user has a vigente asignacion for this materia
        asignaciones = await uow.asignacion.list_by_filters(
            usuario_id=usuario_id,
            materia_id=materia_id,
            vigente=True,
        )

        if not asignaciones:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Materia not found or not assigned to current user",
            )

        materia_repo = MateriaRepository(db, tenant_id)
        m = await materia_repo.get_by_id(materia_id)
        if m is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Materia not found",
            )

        comisiones: set[str] = set()
        cohorte_nombre = ""
        for a in asignaciones:
            comisiones.update(a.comisiones)
            if a.cohorte_id and not cohorte_nombre:
                c = await uow.cohorte.get_by_id(a.cohorte_id)
                if c is not None:
                    cohorte_nombre = str(c.nombre)

        return MateriaResponse(
            id=m.id,
            nombre=m.nombre,
            cohorte=cohorte_nombre,
            comisiones=sorted(comisiones),
            tenant_id=tenant_id,
        )
