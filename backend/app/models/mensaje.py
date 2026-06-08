"""Mensaje model — an individual message within a thread.

Each message belongs to a HiloMensaje thread and has a sender (remitente)
and a receiver (destinatario). Messages have a read/unread state.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TimestampMixin


class Mensaje(AppModel, TimestampMixin):
    """An individual message within a thread.

    Attributes:
        id: UUID primary key.
        tenant_id: Tenant scope (non-nullable FK).
        hilo_id: FK to the parent HiloMensaje thread.
        remitente_id: FK to the sender Usuario.
        destinatario_id: FK to the receiver Usuario.
        asunto: Message subject (copied from thread for denormalized display).
        cuerpo: Message body text.
        leido: Whether the message has been read by the receiver.
        created_at: When the message was sent.
        updated_at: When the message was last updated.
    """

    __tablename__ = "mensajes"

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    hilo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("hilos_mensajes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    remitente_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    destinatario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    asunto: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    cuerpo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    leido: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Mensaje id={self.id} hilo={self.hilo_id} "
            f"remitente={self.remitente_id} leido={self.leido}>"
        )
