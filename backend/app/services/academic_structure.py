"""Service layer for academic structure CRUD with business rules.

Encapsulates business logic:
- Unique code/nombre enforcement (returns 409 on conflict)
- Cross-tenant validation for referenced entities
- Date range validation for cohortes
- Deactivation validation (reject if active cohortes exist)
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.unit_of_work import UnitOfWork
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.mixins import EstadoAcademico
from app.models.programa_materia import ProgramaMateria
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


class CarreraService:
    """Business logic for Carrera CRUD."""

    def __init__(self, session_or_uow: AsyncSession | UnitOfWork, tenant_id: str | None = None):
        if isinstance(session_or_uow, UnitOfWork):
            self.uow = session_or_uow
            self.session = session_or_uow._session
            self.tenant_id = session_or_uow._tenant_id or ""
        else:
            self.session = session_or_uow
            self.tenant_id = tenant_id or ""
            self.uow = UnitOfWork(session_or_uow, self.tenant_id)
        self.repo = self.uow.carrera  # backward compat alias

    async def create(self, data: CarreraCreate) -> CarreraResponse:
        """Create a new carrera with unique codigo enforcement."""
        existing = await self.repo.find_by_codigo(data.codigo)
        if existing is not None:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"A carrera with codigo '{data.codigo}' already exists in this tenant",
            )
        instance = await self.repo.create(data.model_dump())
        return CarreraResponse.model_validate(instance)

    async def get_by_id(self, id: str) -> CarreraResponse:
        """Get a carrera by ID."""
        instance = await self.repo.get_by_id(id)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Carrera not found",
            )
        return CarreraResponse.model_validate(instance)

    async def list(self) -> list[CarreraResponse]:
        """List all carreras for the tenant."""
        instances = await self.repo.list()
        return [CarreraResponse.model_validate(i) for i in instances]

    async def update(self, id: str, data: CarreraUpdate) -> CarreraResponse:
        """Update a carrera, checking codigo uniqueness if changed."""
        existing = await self.repo.get_by_id(id)
        if existing is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Carrera not found",
            )

        update_dict = data.model_dump(exclude_unset=True)

        # Check codigo uniqueness if being changed
        if "codigo" in update_dict and update_dict["codigo"] is not None:
            conflict = await self.repo.find_by_codigo(update_dict["codigo"])
            if conflict is not None and conflict.id != id:
                raise HTTPException(
                    status_code=HTTP_409_CONFLICT,
                    detail=f"A carrera with codigo '{update_dict['codigo']}' already exists",
                )

        # Prevent deactivation if active cohortes exist
        if "estado" in update_dict and update_dict["estado"] == EstadoAcademico.INACTIVA.value:
            active_count = await self.repo.count_active_cohortes(id)
            if active_count > 0:
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cannot deactivate carrera with active cohortes",
                )

        instance = await self.repo.update(id, update_dict)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Carrera not found",
            )
        return CarreraResponse.model_validate(instance)


class CohorteService:
    """Business logic for Cohorte CRUD."""

    def __init__(self, session_or_uow: AsyncSession | UnitOfWork, tenant_id: str | None = None):
        if isinstance(session_or_uow, UnitOfWork):
            self.uow = session_or_uow
            self.session = session_or_uow._session
            self.tenant_id = session_or_uow._tenant_id or ""
        else:
            self.session = session_or_uow
            self.tenant_id = tenant_id or ""
            self.uow = UnitOfWork(session_or_uow, self.tenant_id)
        self.repo = self.uow.cohorte  # backward compat alias

    async def create(self, data: CohorteCreate) -> CohorteResponse:
        """Create a cohorte with uniqueness + cross-tenant validation."""
        # Verify carrera belongs to the same tenant
        carrera = await self.uow.carrera.get_by_id(data.carrera_id)
        if carrera is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Carrera not found",
            )

        # Check nombre uniqueness within carrera+tenant
        existing = await self.repo.find_by_nombre_in_carrera(
            data.nombre, data.carrera_id
        )
        if existing is not None:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"A cohorte with nombre '{data.nombre}' already exists "
                       f"in this carrera",
            )

        instance = await self.repo.create(data.model_dump())
        return CohorteResponse.model_validate(instance)

    async def get_by_id(self, id: str) -> CohorteResponse:
        """Get a cohorte by ID."""
        instance = await self.repo.get_by_id(id)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Cohorte not found",
            )
        return CohorteResponse.model_validate(instance)

    async def list_by_carrera(
        self, carrera_id: str | None = None
    ) -> list[CohorteResponse]:
        """List cohortes, optionally filtered by carrera_id."""
        instances = await self.repo.list_by_carrera(carrera_id)
        return [CohorteResponse.model_validate(i) for i in instances]

    async def update(self, id: str, data: CohorteUpdate) -> CohorteResponse:
        """Update a cohorte."""
        existing = await self.repo.get_by_id(id)
        if existing is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Cohorte not found",
            )
        instance = await self.repo.update(id, data.model_dump(exclude_unset=True))
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Cohorte not found",
            )
        return CohorteResponse.model_validate(instance)


class MateriaService:
    """Business logic for Materia CRUD."""

    def __init__(self, session_or_uow: AsyncSession | UnitOfWork, tenant_id: str | None = None):
        if isinstance(session_or_uow, UnitOfWork):
            self.uow = session_or_uow
            self.session = session_or_uow._session
            self.tenant_id = session_or_uow._tenant_id or ""
        else:
            self.session = session_or_uow
            self.tenant_id = tenant_id or ""
            self.uow = UnitOfWork(session_or_uow, self.tenant_id)
        self.repo = self.uow.materia  # backward compat alias

    async def create(self, data: MateriaCreate) -> MateriaResponse:
        """Create a new materia with unique codigo enforcement."""
        existing = await self.repo.find_by_codigo(data.codigo)
        if existing is not None:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"A materia with codigo '{data.codigo}' already exists in this tenant",
            )
        instance = await self.repo.create(data.model_dump())
        return MateriaResponse.model_validate(instance)

    async def get_by_id(self, id: str) -> MateriaResponse:
        """Get a materia by ID."""
        instance = await self.repo.get_by_id(id)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Materia not found",
            )
        return MateriaResponse.model_validate(instance)

    async def list(self) -> list[MateriaResponse]:
        """List all materias for the tenant."""
        instances = await self.repo.list()
        return [MateriaResponse.model_validate(i) for i in instances]

    async def update(self, id: str, data: MateriaUpdate) -> MateriaResponse:
        """Update a materia, checking codigo uniqueness if changed."""
        existing = await self.repo.get_by_id(id)
        if existing is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Materia not found",
            )

        update_dict = data.model_dump(exclude_unset=True)

        # Check codigo uniqueness if being changed
        if "codigo" in update_dict and update_dict["codigo"] is not None:
            conflict = await self.repo.find_by_codigo(update_dict["codigo"])
            if conflict is not None and conflict.id != id:
                raise HTTPException(
                    status_code=HTTP_409_CONFLICT,
                    detail=f"A materia with codigo '{update_dict['codigo']}' already exists",
                )

        instance = await self.repo.update(id, update_dict)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Materia not found",
            )
        return MateriaResponse.model_validate(instance)


class ProgramaMateriaService:
    """Business logic for ProgramaMateria upload and management."""

    def __init__(self, session_or_uow: AsyncSession | UnitOfWork, tenant_id: str | None = None):
        if isinstance(session_or_uow, UnitOfWork):
            self.uow = session_or_uow
            self.session = session_or_uow._session
            self.tenant_id = session_or_uow._tenant_id or ""
        else:
            self.session = session_or_uow
            self.tenant_id = tenant_id or ""
            self.uow = UnitOfWork(session_or_uow, self.tenant_id)
        self.repo = self.uow.programa_materia  # backward compat alias

    async def upload(
        self,
        titulo: str,
        materia_id: str,
        carrera_id: str,
        cohorte_id: str,
        file_bytes: bytes,
        filename: str,
    ) -> ProgramaMateriaUploadResponse:
        """Upload a syllabus file and create a ProgramaMateria record.

        In MVP, the file is saved to a local directory.
        The storage reference is the local file path.
        """
        # Verify all referenced entities belong to this tenant
        if not await self.uow.carrera.get_by_id(carrera_id):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Carrera not found")
        if not await self.uow.materia.get_by_id(materia_id):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Materia not found")
        if not await self.uow.cohorte.get_by_id(cohorte_id):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Cohorte not found")

        # Save file locally (MVP)
        upload_dir = "uploads/programas_materia"
        os.makedirs(upload_dir, exist_ok=True)
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1] or ".pdf"
        saved_name = f"{file_id}{ext}"
        file_path = os.path.join(upload_dir, saved_name)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        instance = await self.repo.create({
            "titulo": titulo,
            "materia_id": materia_id,
            "carrera_id": carrera_id,
            "cohorte_id": cohorte_id,
            "referencia_archivo": file_path,
        })
        return ProgramaMateriaUploadResponse.model_validate(instance)

    async def list(
        self,
        materia_id: str | None = None,
        carrera_id: str | None = None,
        cohorte_id: str | None = None,
    ) -> list[ProgramaMateriaResponse]:
        """List programa_materia records with optional filters."""
        filters: dict[str, Any] = {}
        if materia_id is not None:
            filters["materia_id"] = materia_id
        if carrera_id is not None:
            filters["carrera_id"] = carrera_id
        if cohorte_id is not None:
            filters["cohorte_id"] = cohorte_id

        instances = await self.repo.list_by_filters(**filters)
        return [ProgramaMateriaResponse.model_validate(i) for i in instances]

    async def delete(self, id: str) -> None:
        """Delete a programa_materia record (hard delete)."""
        deleted = await self.repo.delete(id)
        if not deleted:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="ProgramaMateria not found",
            )
