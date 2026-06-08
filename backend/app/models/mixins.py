"""Reusable mixins for SQLAlchemy models.

- ``TimestampMixin``: created_at / updated_at audit columns
- ``AuditMixin``: estado enum + deleted_at for soft deletes (replaces SoftDeleteMixin)
- ``TenantMixin``: tenant_id foreign key for multi-tenancy
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class EstadoAcademico(str, enum.Enum):
    """Domain enum for academic entity state — feminine form.

    Uses ``Activa``/``Inactiva`` to match domain language
    (``una carrera activa``, ``una cohorte inactiva``).
    """

    ACTIVA = "Activa"
    INACTIVA = "Inactiva"


class EstadoRegistro(str, enum.Enum):
    """Domain enum for entity state — replaces boolean is_active.

    Values are string-based for readability at the database level.
    Future states (``Suspendido``, ``Bloqueado``) can be added without
    schema changes.
    """

    ACTIVO = "Activo"
    INACTIVO = "Inactivo"


class TimestampMixin:
    """Add ``created_at`` and ``updated_at`` timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AuditMixin:
    """Add soft-delete semantics via ``estado`` enum and ``deleted_at`` timestamp.

    Replaces the old ``SoftDeleteMixin.is_active`` boolean with the domain
    ``EstadoRegistro`` enum (``Activo`` / ``Inactivo``).

    Soft-deleting a row sets ``estado = 'Inactivo'`` and ``deleted_at = now()``.
    Default list queries exclude records with ``estado = 'Inactivo'``.
    """

    estado: Mapped[EstadoRegistro] = mapped_column(
        String(20),
        default=EstadoRegistro.ACTIVO,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )


class TenantMixin:
    """Add ``tenant_id`` column scoping all queries to a tenant.

    The ``tenant_id`` column is nullable because the tenant model itself
    does not reference a parent tenant. **Domain models MUST override**
    ``tenant_id`` to ``nullable=False`` with an explicit ``ForeignKey("tenants.id")``.
    """

    tenant_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
