"""Append-only AuditLog model (E-AUD).

Implements the immutable audit trail. Inherits ONLY from ``AppModel`` and
``TenantMixin`` — no ``TimestampMixin`` (no updated_at) and no ``AuditMixin``
(no soft-delete), because audit records are append-only and must never be
modified after creation.

Append-only enforcement:
- **ORM level**: SQLAlchemy event listener ``reject_audit_update`` raises
  an exception if any code attempts to UPDATE an ``AuditLog`` instance.
- **DB level**: PostgreSQL triggers ``trg_reject_audit_update`` and
  ``trg_reject_audit_delete`` reject UPDATE/DELETE at the database layer.
- **Repository level**: ``AuditRepository`` exposes only ``create()`` and
  ``search()``/``count()`` — no ``update()`` or ``delete()`` methods.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, event, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TenantMixin


class AuditLog(AppModel, TenantMixin):
    """Immutable record of a significant action performed in the system.

    Inherits from ``AppModel`` (UUID id) and ``TenantMixin`` (tenant_id).

    This model deliberately does NOT inherit ``TimestampMixin`` or
    ``AuditMixin`` because:
    - ``updated_at`` would imply mutability (forbidden).
    - ``deleted_at`` / ``estado`` would imply soft-delete (forbidden).

    Attributes:
        id: Auto-generated UUID primary key.
        tenant_id: FK to tenants.id (inherited from TenantMixin, overridden
            to non-nullable).
        fecha_hora: Server-default timestamp of when the action occurred.
        actor_id: FK to usuarios.id — the user who performed the action.
        impersonado_id: FK to usuarios.id — the user being impersonated, if any.
        materia_id: FK to materias.id — the subject context, if any.
        accion: The action code string (from ``AccionAuditoria`` enum).
        detalle: Arbitrary JSON context data (MUST NOT contain PII).
        filas_afectadas: Number of rows/records affected by the action.
        ip: Client IP address (IPv4 or IPv6, max 45 chars).
        user_agent: HTTP User-Agent header value (max 500 chars).
    """

    __tablename__ = "audit_log"

    # Override TenantMixin.tenant_id to be non-nullable
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    actor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    impersonado_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    materia_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materias.id", ondelete="SET NULL"),
        nullable=True,
    )
    accion: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    detalle: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    filas_afectadas: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )


# ── ORM-level append-only enforcement ────────────────────────────────────────


@event.listens_for(AuditLog, "before_update", propagate=True)
def reject_audit_update(mapper, connection, target) -> None:  # noqa: ANN201
    """Prevent ORM-level UPDATE on AuditLog instances.

    Raises:
        Exception: Always — audit_log is append-only.
    """
    msg = "audit_log is append-only: UPDATE is forbidden at the ORM level"
    raise Exception(msg)  # noqa: TRY002
