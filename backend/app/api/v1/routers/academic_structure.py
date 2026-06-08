"""Router for academic structure CRUD endpoints.

All endpoints are protected by ``require_permission("estructura_academica:gestionar")``,
which only ADMIN users have per the RBAC permissions matrix.

Endpoints:
- Carreras: POST/GET/GET{id}/PUT
- Cohortes: POST/GET/GET{id}/PUT
- Materias: POST/GET/GET{id}/PUT
- ProgramasMateria: GET/POST upload/DELETE
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
)

from app.core.unit_of_work import UnitOfWork

from app.core.dependencies import get_current_user, get_db, require_permission
from app.schemas.academic_structure import (
    CarreraCreate,
    CarreraResponse,
    CarreraUpdate,
    CohorteCreate,
    CohorteResponse,
    CohorteUpdate,
    MateriaCreate,
    MateriaResponse,
    MateriaUpdate,
    ProgramaMateriaResponse,
    ProgramaMateriaUploadResponse,
)
from app.services.academic_structure import (
    CarreraService,
    CohorteService,
    MateriaService,
    ProgramaMateriaService,
)

router = APIRouter(tags=["academic-structure"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


# ── Carreras ────────────────────────────────────────────────────────────────


@router.post("/api/admin/carreras", status_code=HTTP_201_CREATED, response_model=CarreraResponse)
async def create_carrera(
    body: CarreraCreate,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CarreraResponse:
    """Create a new academic program."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CarreraService(uow)
        return await service.create(body)


@router.get("/api/admin/carreras", response_model=list[CarreraResponse])
async def list_carreras(
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CarreraResponse]:
    """List all carreras scoped to the current tenant."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CarreraService(uow)
        return await service.list()


@router.get("/api/admin/carreras/{id}", response_model=CarreraResponse)
async def get_carrera(
    id: str,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CarreraResponse:
    """Get a single carrera by ID."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CarreraService(uow)
        return await service.get_by_id(id)


@router.put("/api/admin/carreras/{id}", response_model=CarreraResponse)
async def update_carrera(
    id: str,
    body: CarreraUpdate,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CarreraResponse:
    """Update an existing carrera."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CarreraService(uow)
        return await service.update(id, body)


# ── Cohortes ────────────────────────────────────────────────────────────────


@router.post("/api/admin/cohortes", status_code=HTTP_201_CREATED, response_model=CohorteResponse)
async def create_cohorte(
    body: CohorteCreate,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CohorteResponse:
    """Create a new cohort within a carrera."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CohorteService(uow)
        return await service.create(body)


@router.get("/api/admin/cohortes", response_model=list[CohorteResponse])
async def list_cohortes(
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    carrera_id: Optional[str] = None,
) -> list[CohorteResponse]:
    """List cohortes, optionally filtered by carrera_id."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CohorteService(uow)
        return await service.list_by_carrera(carrera_id)


@router.get("/api/admin/cohortes/{id}", response_model=CohorteResponse)
async def get_cohorte(
    id: str,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CohorteResponse:
    """Get a single cohorte by ID."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CohorteService(uow)
        return await service.get_by_id(id)


@router.put("/api/admin/cohortes/{id}", response_model=CohorteResponse)
async def update_cohorte(
    id: str,
    body: CohorteUpdate,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CohorteResponse:
    """Update an existing cohorte."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = CohorteService(uow)
        return await service.update(id, body)


# ── Materias ────────────────────────────────────────────────────────────────


@router.post("/api/admin/materias", status_code=HTTP_201_CREATED, response_model=MateriaResponse)
async def create_materia(
    body: MateriaCreate,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MateriaResponse:
    """Create a new subject in the catalog."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = MateriaService(uow)
        return await service.create(body)


@router.get("/api/admin/materias", response_model=list[MateriaResponse])
async def list_materias(
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MateriaResponse]:
    """List all materias scoped to the current tenant."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = MateriaService(uow)
        return await service.list()


@router.get("/api/admin/materias/{id}", response_model=MateriaResponse)
async def get_materia(
    id: str,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MateriaResponse:
    """Get a single materia by ID."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = MateriaService(uow)
        return await service.get_by_id(id)


@router.put("/api/admin/materias/{id}", response_model=MateriaResponse)
async def update_materia(
    id: str,
    body: MateriaUpdate,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MateriaResponse:
    """Update an existing materia."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = MateriaService(uow)
        return await service.update(id, body)


# ── ProgramasMateria ────────────────────────────────────────────────────────


@router.get("/api/admin/programas-materia", response_model=list[ProgramaMateriaResponse])
async def list_programas_materia(
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    materia_id: Optional[str] = None,
    carrera_id: Optional[str] = None,
    cohorte_id: Optional[str] = None,
) -> list[ProgramaMateriaResponse]:
    """List programa_materia records, filterable by materia_id, carrera_id, cohorte_id."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ProgramaMateriaService(uow)
        return await service.list(
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
        )


@router.post(
    "/api/admin/programas-materia/upload",
    status_code=HTTP_201_CREATED,
    response_model=ProgramaMateriaUploadResponse,
)
async def upload_programa_materia(
    titulo: Annotated[str, Form(...)],
    materia_id: Annotated[str, Form(...)],
    carrera_id: Annotated[str, Form(...)],
    cohorte_id: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProgramaMateriaUploadResponse:
    """Upload a syllabus PDF for a materia + carrera + cohorte combination."""
    file_bytes = await file.read()
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ProgramaMateriaService(uow)
        return await service.upload(
            titulo=titulo,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            file_bytes=file_bytes,
            filename=file.filename or "programa.pdf",
        )


@router.delete(
    "/api/admin/programas-materia/{id}",
    status_code=HTTP_204_NO_CONTENT,
)
async def delete_programa_materia(
    id: str,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a programa_materia record (hard delete)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ProgramaMateriaService(uow)
        await service.delete(id)
