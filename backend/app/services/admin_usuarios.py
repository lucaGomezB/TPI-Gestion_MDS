"""Service layer for admin user management.

Encapsulates:
- User CRUD with role assignment
- Email uniqueness validation per tenant (RN-01)
- Password hashing via Argon2id (D-01)
- Role name → role ID resolution
- Soft-delete via ``activo=false``
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from app.core.security import hash_password
from app.core.unit_of_work import UnitOfWork
from app.models.mixins import EstadoRegistro
from app.models.usuario import Usuario
from app.schemas.admin_usuarios import (
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)


def _usuario_to_response(usuario: Usuario, roles: list[str]) -> UsuarioResponse:
    """Map a Usuario model instance to a UsuarioResponse schema.

    Args:
        usuario: The ``Usuario`` ORM instance.
        roles: List of role name strings assigned to this user.

    Returns:
        A ``UsuarioResponse`` with all safe fields populated.
    """
    return UsuarioResponse(
        id=usuario.id,
        nombre=usuario.nombre,
        apellidos=usuario.apellidos,
        email=usuario.email,
        roles=roles,
        facturador=usuario.facturador,
        regional=usuario.regional,
        legajo=usuario.legajo,
        legajo_profesional=usuario.legajo_profesional,
        banco=usuario.banco,
        activo=usuario.estado == EstadoRegistro.ACTIVO,
        created_at=usuario.created_at,
        updated_at=usuario.updated_at,
    )


class AdminUsuariosService:
    """Business logic for admin user management.

    Args:
        uow: The ``UnitOfWork`` instance for data access.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.repo = uow.admin_usuarios

    # ── List ──────────────────────────────────────────────────────────────

    async def list_users(self, rol: str | None = None) -> list[UsuarioResponse]:
        """List active users, optionally filtered by role name.

        Args:
            rol: Optional role name filter (e.g. ``"docente"``, ``"PROFESOR"``).

        Returns:
            A list of ``UsuarioResponse`` instances.
        """
        usuarios = await self.repo.list_by_rol(rol_name=rol)

        if not usuarios:
            return []

        # Bulk-fetch roles for all users in one query
        user_ids = [u.id for u in usuarios]
        roles_map = await self.repo.get_roles_for_users(user_ids)

        return [
            _usuario_to_response(u, roles_map.get(u.id, []))
            for u in usuarios
        ]

    # ── Get single user ───────────────────────────────────────────────────

    async def get_user(self, usuario_id: str) -> UsuarioResponse:
        """Get a single user by ID with their role names.

        Args:
            usuario_id: The user UUID.

        Returns:
            A ``UsuarioResponse`` instance.

        Raises:
            HTTPException(404): If the user is not found.
        """
        usuario = await self.repo.get(usuario_id)
        if usuario is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Usuario[{usuario_id}] not found",
            )

        roles = await self.repo.get_roles_for_user(usuario_id)
        return _usuario_to_response(usuario, roles)

    # ── Create ────────────────────────────────────────────────────────────

    async def create_user(self, data: UsuarioCreate) -> UsuarioResponse:
        """Create a new user with role assignments.

        Args:
            data: The ``UsuarioCreate`` payload.

        Returns:
            The created ``UsuarioResponse``.

        Raises:
            HTTPException(409): If the email is already in use within the tenant.
            HTTPException(400): If any role name does not exist in the tenant.
        """
        # Check email uniqueness
        exists = await self.repo.check_email_exists(data.email)
        if exists:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"Email '{data.email}' is already in use",
            )

        # Build the model payload (exclude roles — handled separately)
        payload = data.model_dump(exclude={"roles", "password"})

        # Hash password if provided
        if data.password:
            payload["password_hash"] = hash_password(data.password)

        # Compute email hash
        payload["email_hash"] = Usuario.compute_email_hash(data.email)

        # Create the user
        usuario = await self.repo.create(payload)

        # Assign roles
        await self.repo.set_roles(usuario.id, data.roles)

        roles = await self.repo.get_roles_for_user(usuario.id)
        return _usuario_to_response(usuario, roles)

    # ── Update ────────────────────────────────────────────────────────────

    async def update_user(
        self, usuario_id: str, data: UsuarioUpdate
    ) -> UsuarioResponse:
        """Partially update a user. Only provided fields are changed.

        Args:
            usuario_id: The user UUID.
            data: The ``UsuarioUpdate`` payload.

        Returns:
            The updated ``UsuarioResponse``.

        Raises:
            HTTPException(404): If the user is not found.
            HTTPException(409): If the new email is already in use.
        """
        # Use get_any to allow updates on inactive (soft-deleted) users too
        usuario = await self.repo.get_any(usuario_id)
        if usuario is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Usuario[{usuario_id}] not found",
            )

        update_data = data.model_dump(exclude_unset=True, exclude={"roles", "password", "activo"})

        # Check email uniqueness if changing
        if "email" in update_data and update_data["email"] != usuario.email:
            exists = await self.repo.check_email_exists(
                update_data["email"], exclude_id=usuario_id
            )
            if exists:
                raise HTTPException(
                    status_code=HTTP_409_CONFLICT,
                    detail=f"Email '{update_data['email']}' is already in use",
                )
            update_data["email_hash"] = Usuario.compute_email_hash(update_data["email"])

        # Hash new password if provided
        if data.password is not None:
            if data.password:
                update_data["password_hash"] = hash_password(data.password)
            # If password is empty string, leave password_hash unchanged

        # Handle activo flag → estado mapping
        if data.activo is False:
            # Soft-delete — directly update local object (BaseRepository.get()
            # would not find an inactive record)
            await self.repo.soft_delete(usuario_id)
            usuario.estado = EstadoRegistro.INACTIVO
            usuario.deleted_at = datetime.now(timezone.utc)
            # Skip scalar updates when soft-deleting
            update_data.clear()
        elif data.activo is True:
            # Reactivate — use unscoped update that includes inactive records
            update_data["estado"] = EstadoRegistro.ACTIVO
            update_data["deleted_at"] = None

        # Apply scalar field updates
        if update_data:
            usuario = await self.repo.update_any(usuario_id, update_data)
            if usuario is None:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Usuario[{usuario_id}] not found during update",
                )

        # Update roles if provided
        if data.roles is not None:
            await self.repo.set_roles(usuario_id, data.roles)

        roles = await self.repo.get_roles_for_user(usuario_id)
        return _usuario_to_response(usuario, roles)
