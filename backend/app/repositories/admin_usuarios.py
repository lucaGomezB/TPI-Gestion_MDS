"""Repository for admin user management — role filtering and role assignments.

Extends ``BaseRepository[Usuario]`` with:
- Role-based user filtering (join through UsuarioRol → Rol)
- Bulk role assignment/replacement
- Duplicate email detection per tenant
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mixins import EstadoRegistro
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol
from app.repositories.base import BaseRepository


class AdminUsuariosRepository(BaseRepository[Usuario]):
    """Repository for admin user management with role-aware queries.

    Args:
        session: An active SQLAlchemy ``AsyncSession``.
        tenant_id: The tenant UUID for scoping all queries.
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = Usuario

    # ── Role-based listing ────────────────────────────────────────────────

    async def list_by_rol(self, rol_name: str | None = None) -> list[Usuario]:
        """List active users, optionally filtered by role name.

        When ``rol_name`` is provided, only users assigned that role
        (via UsuarioRol → Rol) are returned. Otherwise, all active users
        in the tenant are returned.

        Args:
            rol_name: Optional role name string (e.g. ``"docente"``, ``"PROFESOR"``).

        Returns:
            A list of ``Usuario`` instances.
        """
        stmt: Select = (
            select(Usuario)
            .where(Usuario.tenant_id == self.tenant_id)
            .where(Usuario.estado == EstadoRegistro.ACTIVO)
        )

        if rol_name:
            stmt = (
                stmt
                .join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
                .join(Rol, Rol.id == UsuarioRol.rol_id)
                .where(Rol.nombre == rol_name)
                .where(UsuarioRol.tenant_id == self.tenant_id)
            )

        stmt = stmt.order_by(Usuario.apellidos, Usuario.nombre)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── User with roles ───────────────────────────────────────────────────

    async def get_roles_for_user(self, usuario_id: str) -> list[str]:
        """Get all role names assigned to a user.

        Args:
            usuario_id: The user UUID.

        Returns:
            A list of role name strings (e.g. ``["PROFESOR", "TUTOR"]``).
        """
        result = await self.session.execute(
            select(Rol.nombre)
            .select_from(UsuarioRol)
            .join(Rol, UsuarioRol.rol_id == Rol.id)
            .where(
                UsuarioRol.usuario_id == usuario_id,
                UsuarioRol.tenant_id == self.tenant_id,
            )
        )
        return list(result.scalars().all())

    # ── Role assignment ───────────────────────────────────────────────────

    async def set_roles(self, usuario_id: str, role_names: list[str]) -> None:
        """Replace all role assignments for a user.

        Deletes all existing ``UsuarioRol`` rows for the user within the
        tenant, then inserts new ones for each role name in ``role_names``.

        Roles that don't exist in the tenant are silently skipped.

        Args:
            usuario_id: The user UUID.
            role_names: List of role name strings to assign.
        """
        # Delete existing roles for this user in this tenant
        await self.session.execute(
            delete(UsuarioRol).where(
                UsuarioRol.usuario_id == usuario_id,
                UsuarioRol.tenant_id == self.tenant_id,
            )
        )

        if not role_names:
            return

        # Resolve role IDs for the given names within the tenant
        result = await self.session.execute(
            select(Rol.id, Rol.nombre).where(
                Rol.tenant_id == self.tenant_id,
                Rol.nombre.in_(role_names),
            )
        )
        role_map = {row.nombre: row.id for row in result}

        now = datetime.now(timezone.utc)
        for name in role_names:
            rol_id = role_map.get(name)
            if rol_id is None:
                continue
            self.session.add(
                UsuarioRol(
                    usuario_id=usuario_id,
                    rol_id=rol_id,
                    tenant_id=self.tenant_id,
                    created_at=now,
                )
            )

        await self.session.flush()

    # ── Duplicate detection ────────────────────────────────────────────────

    async def check_email_exists(
        self, email: str, exclude_id: str | None = None
    ) -> bool:
        """Check if an email is already in use within the tenant.

        Uses ``email_hash`` for the lookup (avoids decrypting the column).

        Args:
            email: The plaintext email to check.
            exclude_id: Optional user UUID to exclude (for update checks).

        Returns:
            ``True`` if the email is already taken, ``False`` otherwise.
        """
        email_hash = Usuario.compute_email_hash(email)
        stmt = select(Usuario.id).where(
            Usuario.tenant_id == self.tenant_id,
            Usuario.email_hash == email_hash,
            Usuario.estado == EstadoRegistro.ACTIVO,
        )
        if exclude_id:
            stmt = stmt.where(Usuario.id != exclude_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    # ── Unscoped operations (include inactive records) ─────────────────────

    async def get_any(self, usuario_id: str) -> Usuario | None:
        """Get a user by ID regardless of estado (includes soft-deleted).

        Unlike ``BaseRepository.get()``, this does NOT filter out inactive
        records. Used during update/reactivation flows.

        Args:
            usuario_id: The user UUID.

        Returns:
            The ``Usuario`` instance or ``None`` if not found.
        """
        stmt = (
            select(Usuario)
            .where(Usuario.id == usuario_id)
            .where(Usuario.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_any(self, usuario_id: str, data: dict) -> Usuario | None:
        """Update a user regardless of estado (includes soft-deleted).

        Unlike ``BaseRepository.update()``, this does NOT filter out inactive
        records. Used for reactivation flows.

        Args:
            usuario_id: The user UUID.
            data: Dict of fields to update.

        Returns:
            The updated ``Usuario`` instance or ``None`` if not found.
        """
        stmt = (
            update(Usuario)
            .where(Usuario.id == usuario_id)
            .where(Usuario.tenant_id == self.tenant_id)
            .values(**data)
            .returning(Usuario)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Bulk role resolution ───────────────────────────────────────────────

    async def get_roles_for_users(self, usuario_ids: list[str]) -> dict[str, list[str]]:
        """Get role names for multiple users in a single query.

        Args:
            usuario_ids: List of user UUIDs.

        Returns:
            Dict mapping ``usuario_id`` → list of role name strings.
        """
        if not usuario_ids:
            return {}

        result = await self.session.execute(
            select(UsuarioRol.usuario_id, Rol.nombre)
            .join(Rol, UsuarioRol.rol_id == Rol.id)
            .where(
                UsuarioRol.usuario_id.in_(usuario_ids),
                UsuarioRol.tenant_id == self.tenant_id,
            )
        )

        role_map: dict[str, list[str]] = {uid: [] for uid in usuario_ids}
        for row in result:
            role_map.setdefault(row.usuario_id, []).append(row.nombre)
        return role_map
