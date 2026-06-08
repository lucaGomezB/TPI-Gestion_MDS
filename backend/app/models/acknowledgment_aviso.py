"""AcknowledgmentAviso model — append-only acknowledgment log for avisos.

Per D-04 in design.md, this is an append-only log: records are inserted
once and never modified or deleted. A unique constraint on (aviso_id, usuario_id)
provides DB-level idempotency (RN-19).
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TenantMixin


class AcknowledgmentAviso(AppModel, TenantMixin):
    """Log entry recording that a user acknowledged reading an aviso (RN-19).

    This is an immutable audit record — once created, it is never modified.
    The unique constraint on (aviso_id, usuario_id) ensures idempotency.

    Attributes:
        id: UUID primary key.
        tenant_id: Tenant scope (FK to tenants).
        aviso_id: FK to the acknowledged aviso (CASCADE delete).
        usuario_id: FK to the acknowledging user (CASCADE delete).
        leido_en: Timestamp of when the user confirmed reading.
    """

    __tablename__ = "acknowledgments_avisos"

    __table_args__ = (
        UniqueConstraint(
            "aviso_id",
            "usuario_id",
            name="uq_ack_aviso_usuario",
        ),
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    aviso_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("avisos.id", ondelete="CASCADE"),
        nullable=False,
    )
    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    leido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<AcknowledgmentAviso aviso={self.aviso_id} "
            f"usuario={self.usuario_id} leido_en={self.leido_en}>"
        )
