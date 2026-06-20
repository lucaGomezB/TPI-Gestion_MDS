"""Service layer for admin role management.

Encapsulates:
- Role CRUD with permission management
- Name uniqueness validation per tenant
- Soft-delete/reactivation with in-use check
- Permission validation against known set
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from app.core.permissions import ALL_PERMISSIONS
from app.core.unit_of_work import UnitOfWork
from app.models.mixins import EstadoRegistro
from app.models.rol import Rol
from app.schemas.admin_roles import (
    RolCreate,
    RolResponse,
    RolUpdate,
)


def _rol_to_response(rol: Rol) -> RolResponse:
    """Map a Rol model instance to a RolResponse schema.

    Args:
        rol: The ``Rol`` ORM instance.

    Returns:
        A ``RolResponse`` with all safe fields populated.
    """
    return RolResponse(
        id=rol.id,
        nombre=rol.nombre,
        descripcion=rol.descripcion,
        permisos=rol.permisos,
        activo=rol.estado == EstadoRegistro.ACTIVO,
        created_at=rol.created_at,
        updated_at=rol.updated_at,
    )


def _validate_permisos(permisos: list[str]) -> None:
    """Validate that all permission strings are known.

    Args:
        permisos: List of permission strings to validate.

    Raises:
        HTTPException(400): If any permission is not in ALL_PERMISSIONS.
    """
    unknown = [p for p in permisos if p not in ALL_PERMISSIONS]
    if unknown:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Unknown permissions: {', '.join(unknown)}",
        )


class AdminRolesService:
    """Business logic for admin role management.

    Args:
        uow: The ``UnitOfWork`` instance for data access.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.repo = uow.admin_roles

    # ── List ──────────────────────────────────────────────────────────────

    async def list_roles(self) -> list[RolResponse]:
        """List all active roles in the tenant.

        Returns:
            A list of ``RolResponse`` instances.
        """
        roles = await self.repo.list_all()
        return [_rol_to_response(r) for r in roles]

    # ── Get single role ───────────────────────────────────────────────────

    async def get_role(self, rol_id: str) -> RolResponse:
        """Get a single role by ID.

        Args:
            rol_id: The role UUID.

        Returns:
            A ``RolResponse`` instance.

        Raises:
            HTTPException(404): If the role is not found.
        """
        rol = await self.repo.get(rol_id)
        if rol is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Role[{rol_id}] not found",
            )
        return _rol_to_response(rol)

    # ── Create ────────────────────────────────────────────────────────────

    async def create_role(self, data: RolCreate) -> RolResponse:
        """Create a new role with permissions.

        Args:
            data: The ``RolCreate`` payload.

        Returns:
            The created ``RolResponse``.

        Raises:
            HTTPException(409): If the role name is already in use within the tenant.
            HTTPException(400): If any permission is unknown.
        """
        # Validate permissions
        _validate_permisos(data.permisos)

        # Check name uniqueness
        exists = await self.repo.check_name_exists(data.nombre)
        if exists:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"Role name '{data.nombre}' is already in use",
            )

        # Build payload
        payload = {
            "nombre": data.nombre,
            "descripcion": data.descripcion,
            "permisos": data.permisos,
        }

        rol = await self.repo.create(payload)
        return _rol_to_response(rol)

    # ── Update ────────────────────────────────────────────────────────────

    async def update_role(
        self, rol_id: str, data: RolUpdate
    ) -> RolResponse:
        """Partially update a role. Only provided fields are changed.

        Args:
            rol_id: The role UUID.
            data: The ``RolUpdate`` payload.

        Returns:
            The updated ``RolResponse``.

        Raises:
            HTTPException(404): If the role is not found.
            HTTPException(409): If the new name is already in use.
            HTTPException(400): If permissions are unknown or role is in use on delete.
        """
        rol = await self.repo.get_any(rol_id)
        if rol is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Role[{rol_id}] not found",
            )

        update_data = data.model_dump(exclude_unset=True, exclude={"permisos", "activo"})

        # Handle name change with uniqueness check
        if "nombre" in update_data and update_data["nombre"] != rol.nombre:
            exists = await self.repo.check_name_exists(
                update_data["nombre"], exclude_id=rol_id
            )
            if exists:
                raise HTTPException(
                    status_code=HTTP_409_CONFLICT,
                    detail=f"Role name '{update_data['nombre']}' is already in use",
                )

        # Handle permisos update
        if data.permisos is not None:
            _validate_permisos(data.permisos)
            update_data["permisos"] = data.permisos

        # Handle activo flag → estado mapping
        if data.activo is False:
            # Check if role is in use before soft-delete
            in_use = await self.repo.is_role_in_use(rol_id)
            if in_use:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail="Cannot delete a role that is currently assigned to users",
                )
            await self.repo.soft_delete(rol_id)
            rol.estado = EstadoRegistro.INACTIVO
            rol.deleted_at = datetime.now(timezone.utc)
            update_data.clear()
        elif data.activo is True:
            update_data["estado"] = EstadoRegistro.ACTIVO
            update_data["deleted_at"] = None

        # Apply scalar field updates
        if update_data:
            updated = await self.repo.update(rol_id, update_data)
            if updated is None:
                # Reactivation case: entity is inactive, use unscoped update
                updated = await self.repo.update_any(rol_id, update_data)

            if updated is None:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Role[{rol_id}] not found during update",
                )
            rol = updated

        return _rol_to_response(rol)

    # ── Delete (soft) ─────────────────────────────────────────────────────

    async def delete_role(self, rol_id: str) -> None:
        """Soft-delete a role by ID.

        Args:
            rol_id: The role UUID.

        Raises:
            HTTPException(404): If the role is not found.
            HTTPException(400): If the role is currently assigned to users.
        """
        # Check if role exists (active)
        rol = await self.repo.get(rol_id)
        if rol is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Role[{rol_id}] not found",
            )

        # Check if role is in use
        in_use = await self.repo.is_role_in_use(rol_id)
        if in_use:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Cannot delete a role that is currently assigned to users",
            )

        await self.repo.soft_delete(rol_id)
