"""UsuarioRol model — assigns a role to a user within a tenant.

Supports temporal validity via ``vigencia_desde`` and ``vigencia_hasta``
to model seasonal assignments (e.g., a professor assigned to a role only
during a specific academic term).

Unique constraint on ``(usuario_id, rol_id)`` prevents duplicate assignments.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel


class UsuarioRol(AppModel):
    """Links a user to a role within a tenant, with optional temporal validity."""

    __tablename__ = "usuario_roles"

    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    rol_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    vigencia_desde: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    vigencia_hasta: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    # ── Constraints ──────────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "rol_id",
            name="uq_usuario_rol",
        ),
    )
