"""Service layer for team management with business rules.

Encapsulates business logic:
- Individual / bulk / clone assignment operations
- Vigencia state computation (Pendiente / Vigente / Vencida)
- Cross-tenant validation for referenced entities
- CSV export generation
"""

import csv
import io
from datetime import date, datetime
from typing import Any

from fastapi import HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.core.unit_of_work import UnitOfWork
from app.models.asignacion import Asignacion
from app.models.usuario import Usuario
from app.schemas.team_management import (
    AsignacionCreate,
    AsignacionMasivaRequest,
    AsignacionMasivaResponse,
    AsignacionResponse,
    AsignacionUpdate,
    ClonarRequest,
    ClonarResponse,
    EquipoExportRow,
    VigenciaRequest,
    VigenciaResponse,
)


def _compute_estado_vigencia(vig_desde: date, vig_hasta: date | None, today: date | None = None) -> str:
    """Compute the derived vigencia state from date fields.

    Per D-06:
    - Pendiente: today < vig_desde
    - Vigente: vig_desde <= today <= vig_hasta (or vig_hasta is NULL)
    - Vencida: today > vig_hasta
    """
    if today is None:
        today = date.today()
    if vig_hasta is not None and today > vig_hasta:
        return "Vencida"
    if today < vig_desde:
        return "Pendiente"
    return "Vigente"


def _asignacion_to_response(instance: Asignacion) -> AsignacionResponse:
    """Convert an Asignacion model instance to its response schema with computed state."""
    return AsignacionResponse(
        id=instance.id,
        tenant_id=instance.tenant_id,
        usuario_id=instance.usuario_id,
        rol=instance.rol,
        materia_id=instance.materia_id,
        carrera_id=instance.carrera_id,
        cohorte_id=instance.cohorte_id,
        comisiones=list(instance.comisiones) if instance.comisiones else [],
        responsable_id=instance.responsable_id,
        vig_desde=instance.vig_desde,
        vig_hasta=instance.vig_hasta,
        estado_vigencia=_compute_estado_vigencia(instance.vig_desde, instance.vig_hasta),
        created_at=instance.created_at,
        updated_at=instance.updated_at,
    )


class TeamManagementService:
    """Business logic for team management."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.tenant_id = uow._tenant_id or ""
        self.repo = uow.asignacion  # backward compat alias

    # ── Validation helpers ────────────────────────────────────────────

    async def _validate_academic_context(
        self,
        materia_id: str | None,
        carrera_id: str | None,
        cohorte_id: str | None,
    ) -> None:
        """Validate that all FK references belong to the same tenant.

        Raises:
            HTTPException(404) if any referenced entity does not exist
            in the current tenant.
        """
        if materia_id is not None:
            if not await self.uow.materia.get_by_id(materia_id):
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail="Materia not found",
                )
        if carrera_id is not None:
            if not await self.uow.carrera.get_by_id(carrera_id):
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail="Carrera not found",
                )
        if cohorte_id is not None:
            if not await self.uow.cohorte.get_by_id(cohorte_id):
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail="Cohorte not found",
                )

    async def _validate_usuarios_exist(self, usuario_ids: list[str]) -> list[Usuario]:
        """Validate that all usuario_ids exist in the current tenant.

        Returns:
            List of Usuario instances.

        Raises:
            HTTPException(404) if any usuario_id is not found.
        """
        from sqlalchemy import select

        result = await self.uow._session.execute(
            select(Usuario).where(
                Usuario.id.in_(usuario_ids),
                Usuario.tenant_id == self.tenant_id,
            )
        )
        found = list(result.scalars().all())
        found_ids = {u.id for u in found}
        missing = [uid for uid in usuario_ids if uid not in found_ids]
        if missing:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Usuarios not found: {', '.join(missing)}",
            )
        return found

    async def _validate_create_payload(
        self, usuario_id: str, rol: str, materia_id: str | None, carrera_id: str | None,
        cohorte_id: str | None, responsable_id: str | None,
    ) -> None:
        """Validate FK references for a single assignment payload."""
        await self._validate_usuarios_exist([usuario_id])
        await self._validate_academic_context(materia_id, carrera_id, cohorte_id)
        if responsable_id is not None:
            await self._validate_usuarios_exist([responsable_id])

    # ── CRUD operations ───────────────────────────────────────────────

    async def create_asignacion(self, data: AsignacionCreate) -> AsignacionResponse:
        """Create a single assignment with FK validation."""
        await self._validate_create_payload(
            usuario_id=data.usuario_id,
            rol=data.rol.value if hasattr(data.rol, 'value') else str(data.rol),
            materia_id=data.materia_id,
            carrera_id=data.carrera_id,
            cohorte_id=data.cohorte_id,
            responsable_id=data.responsable_id,
        )

        instance = await self.repo.create(data.model_dump())
        return _asignacion_to_response(instance)

    async def get_asignacion(self, id: str) -> AsignacionResponse:
        """Get a single assignment by ID."""
        instance = await self.repo.get(id)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Asignacion not found",
            )
        return _asignacion_to_response(instance)

    async def list_asignaciones(
        self,
        usuario_id: str | None = None,
        materia_id: str | None = None,
        carrera_id: str | None = None,
        cohorte_id: str | None = None,
        rol: str | None = None,
        vigente: bool | None = None,
    ) -> list[AsignacionResponse]:
        """List assignments with optional filters and computed estado_vigencia."""
        instances = await self.repo.list_by_filters(
            usuario_id=usuario_id,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            rol=rol,
            vigente=vigente,
        )
        return [_asignacion_to_response(i) for i in instances]

    async def update_asignacion(self, id: str, data: AsignacionUpdate) -> AsignacionResponse:
        """Partially update an assignment."""
        existing = await self.repo.get(id)
        if existing is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Asignacion not found",
            )

        update_dict = data.model_dump(exclude_unset=True)

        # If rol is being updated, ensure it's stored as string
        if "rol" in update_dict and update_dict["rol"] is not None:
            rol_val = update_dict["rol"]
            update_dict["rol"] = rol_val.value if hasattr(rol_val, 'value') else str(rol_val)

        # Validate new FK references if changed
        if "responsable_id" in update_dict and update_dict["responsable_id"] is not None:
            await self._validate_usuarios_exist([update_dict["responsable_id"]])
        if "materia_id" in update_dict and update_dict["materia_id"] is not None:
            if not await self.uow.materia.get_by_id(update_dict["materia_id"]):
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Materia not found")

        instance = await self.repo.update(id, update_dict)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Asignacion not found",
            )
        return _asignacion_to_response(instance)

    # ── Bulk assignment (D-07) ────────────────────────────────────────

    async def asignacion_masiva(self, request: AsignacionMasivaRequest) -> AsignacionMasivaResponse:
        """Assign multiple usuarios to the same academic context.

        Transactional: validates all FK references first, then creates all
        assignments. Rolls back on any validation failure.
        """
        # Validate all usuario_ids exist in this tenant
        await self._validate_usuarios_exist(request.usuario_ids)

        # Validate academic context
        await self._validate_academic_context(
            request.materia_id, request.carrera_id, request.cohorte_id,
        )

        # Validate responsable if provided
        if request.responsable_id is not None:
            await self._validate_usuarios_exist([request.responsable_id])

        # Build entries with common parameters
        base = request.model_dump(exclude={"usuario_ids"})
        rol_str = base["rol"].value if hasattr(base["rol"], 'value') else str(base["rol"])
        base["rol"] = rol_str

        entries = []
        for uid in request.usuario_ids:
            entry = {**base, "usuario_id": uid}
            entries.append(entry)

        instances = await self.repo.bulk_create(entries)
        responses = [_asignacion_to_response(i) for i in instances]
        return AsignacionMasivaResponse(creadas=responses, total=len(responses))

    # ── Clone equipo (D-08) ───────────────────────────────────────────

    async def clonar_equipo(self, request: ClonarRequest) -> ClonarResponse:
        """Clone all Vigente assignments from a source to a destination context.

        Validates source != destination (handled by schema),
        validates destination FKs, and copies assignments.
        """
        # Validate destination context
        await self._validate_academic_context(
            request.destino_materia_id,
            request.destino_carrera_id,
            request.destino_cohorte_id,
        )

        # Fetch vigente assignments from source
        source_assignments = await self.repo.find_vigentes_by_equipo(
            request.origen_materia_id,
            request.origen_carrera_id,
            request.origen_cohorte_id,
        )

        if not source_assignments:
            return ClonarResponse(clonadas=0)

        # Build entries for destination
        entries = []
        for src in source_assignments:
            entries.append({
                "usuario_id": src.usuario_id,
                "rol": src.rol,
                "materia_id": request.destino_materia_id,
                "carrera_id": request.destino_carrera_id,
                "cohorte_id": request.destino_cohorte_id,
                "comisiones": src.comisiones,
                "responsable_id": src.responsable_id,
                "vig_desde": date.today(),
                "vig_hasta": None,
            })

        instances = await self.repo.bulk_create(entries)
        return ClonarResponse(clonadas=len(instances))

    # ── Bulk vigencia update (D-09) ────────────────────────────────────

    async def actualizar_vigencia(self, request: VigenciaRequest) -> VigenciaResponse:
        """Bulk update vigencia dates for all assignments matching the equipo scope."""
        updated = await self.repo.update_vigencia(
            materia_id=request.materia_id,
            carrera_id=request.carrera_id,
            cohorte_id=request.cohorte_id,
            vig_desde=request.vig_desde,
            vig_hasta=request.vig_hasta,
        )
        return VigenciaResponse(actualizadas=updated)

    # ── Export (D-10) ─────────────────────────────────────────────────

    async def exportar_equipo(
        self,
        materia_id: str | None,
        carrera_id: str | None,
        cohorte_id: str | None,
    ) -> str:
        """Generate CSV content for the teaching team of a given academic context.

        Returns:
            CSV string with header and data rows.
        """
        if not any([materia_id, carrera_id, cohorte_id]):
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one filter parameter (materia_id, carrera_id, cohorte_id) is required",
            )

        rows = await self.repo.export_equipo_data(materia_id, carrera_id, cohorte_id)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "docente_nombre",
            "docente_apellidos",
            "docente_email",
            "rol",
            "comisiones",
            "responsable_nombre",
            "vig_desde",
            "vig_hasta",
            "estado_vigencia",
        ])

        for asignacion, usuario, responsable in rows:
            writer.writerow([
                usuario.nombre if hasattr(usuario, 'nombre') else "",
                usuario.apellidos if hasattr(usuario, 'apellidos') else "",
                usuario.email if hasattr(usuario, 'email') else "",
                asignacion.rol,
                ";".join(asignacion.comisiones) if asignacion.comisiones else "",
                f"{responsable.nombre} {responsable.apellidos}".strip()
                if responsable else "",
                asignacion.vig_desde.isoformat(),
                asignacion.vig_hasta.isoformat() if asignacion.vig_hasta else "",
                _compute_estado_vigencia(asignacion.vig_desde, asignacion.vig_hasta),
            ])

        return output.getvalue()
