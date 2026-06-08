"""MensajeEliminado model — per-user soft-delete tracking for messages.

Per Decision 4 from design.md: In messaging, deleting a message for one user
should not affect the other user. This model tracks which user deleted which
message, so both parties can independently control their view.

This model does NOT inherit TimestampMixin because it is an audit record —
created_at is the only meaningful timestamp.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel


class MensajeEliminado(AppModel):
    """Tracks which user soft-deleted which message.

    Attributes:
        id: UUID primary key.
        mensaje_id: FK to the deleted Mensaje.
        usuario_id: FK to the Usuario who deleted it.
        created_at: When the deletion record was created.
    """

    __tablename__ = "mensajes_eliminados"

    mensaje_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("mensajes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<MensajeEliminado mensaje={self.mensaje_id} "
            f"usuario={self.usuario_id}>"
        )
