"""Repository for admin role management — role CRUD with name uniqueness checks.

Extends ``BaseRepository[Rol]`` with:
- Duplicate name detection per tenant
- Active/inactive role queries
"""

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.mixins import EstadoRegistro
from app.models.rol import Rol
from app.models.usuario_rol import UsuarioRol
from app.repositories.base import BaseRepository


class AdminRolesRepository(BaseRepository[Rol]):
    """Repository for admin role management with name uniqueness checks.

    Args:
        session: An active SQLAlchemy ``AsyncSession``.
        tenant_id: The tenant UUID for scoping all queries.
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = Rol

    # ── Override _stmt to exclude soft-deleted on list/get ──────────────────

    async def list_all(self) -> list[Rol]:
        """List all active roles in the tenant, ordered by name.

        Returns:
            A list of ``Rol`` instances.
        """
        stmt: Select = (
            select(Rol)
            .where(Rol.tenant_id == self.tenant_id)
            .where(Rol.estado == EstadoRegistro.ACTIVO)
            .order_by(Rol.nombre)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Get any (includes soft-deleted) ─────────────────────────────────────

    async def get_any(self, rol_id: str) -> Rol | None:
        """Get a role by ID regardless of estado (includes soft-deleted).

        Unlike ``BaseRepository.get()``, this does NOT filter out inactive
        records. Used during update/reactivation flows.

        Args:
            rol_id: The role UUID.

        Returns:
            The ``Rol`` instance or ``None`` if not found.
        """
        stmt = (
            select(Rol)
            .where(Rol.id == rol_id)
            .where(Rol.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Name uniqueness ─────────────────────────────────────────────────────

    async def check_name_exists(
        self, nombre: str, exclude_id: str | None = None
    ) -> bool:
        """Check if a role name is already in use within the tenant.

        Args:
            nombre: The role name to check.
            exclude_id: Optional role UUID to exclude (for update checks).

        Returns:
            ``True`` if the name is already taken, ``False`` otherwise.
        """
        stmt = select(Rol.id).where(
            Rol.tenant_id == self.tenant_id,
            Rol.nombre == nombre,
            Rol.estado == EstadoRegistro.ACTIVO,
        )
        if exclude_id:
            stmt = stmt.where(Rol.id != exclude_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    # ── Check if role is in use ─────────────────────────────────────────────

    async def is_role_in_use(self, rol_id: str) -> bool:
        """Check if a role is currently assigned to at least one user.

        Args:
            rol_id: The role UUID to check.

        Returns:
            ``True`` if the role has at least one UsuarioRol assignment.
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(UsuarioRol)
            .where(
                UsuarioRol.rol_id == rol_id,
                UsuarioRol.tenant_id == self.tenant_id,
            )
        )
        count = result.scalar_one()
        return count > 0

    # ── Unscoped update (includes inactive records) ─────────────────────────

    async def update_any(self, rol_id: str, data: dict) -> Rol | None:
        """Update a role regardless of estado (includes soft-deleted).

        Unlike ``BaseRepository.update()``, this does NOT filter out inactive
        records. Used for reactivation flows.

        Args:
            rol_id: The role UUID.
            data: Dict of fields to update.

        Returns:
            The updated ``Rol`` instance or ``None`` if not found.
        """
        from sqlalchemy import update

        stmt = (
            update(Rol)
            .where(Rol.id == rol_id)
            .where(Rol.tenant_id == self.tenant_id)
            .values(**data)
            .returning(Rol)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
