"""Rol model — catalog of named roles within a tenant.

Each role groups a set of permissions (``modulo:accion`` strings).
Roles are tenant-scoped: the same name can exist in different tenants
with different permission sets.

Unique constraint on ``(tenant_id, nombre)`` ensures no duplicate role
names within a tenant.
"""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import AuditMixin, TenantMixin, TimestampMixin


class Rol(AppModel, TimestampMixin, TenantMixin, AuditMixin):
    """A named role that groups a set of permissions within a tenant."""

    __tablename__ = "roles"

    # ── Override TenantMixin.tenant_id to be non-nullable ────────────
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Fields ───────────────────────────────────────────────────────
    nombre: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    descripcion: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    permisos: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # ── Constraints ──────────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "nombre",
            name="uq_rol_tenant_nombre",
        ),
    )
