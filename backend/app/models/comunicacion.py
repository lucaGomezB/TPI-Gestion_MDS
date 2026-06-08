"""Comunicacion and LoteComunicacion models — communications queue.

Defines the two entities for the bulk email communication system:
- ``LoteComunicacion``: A batch of communications sent together.
- ``Comunicacion``: A single email message to one recipient.

Lifecycle per RN-15, D-01, D-02:
- Comunicacion: Pendiente -> Enviando -> Enviado/Error/Cancelado
- LoteComunicacion: Pendiente -> AprobacionPendiente -> Enviando -> Completado/Parcial/Cancelado

Neither model inherits ``AuditMixin`` (no soft-delete). Communication records
are immutable history — once created, they are never deleted.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin
from app.models.types import EncryptedString


class EstadoComunicacion(str, enum.Enum):
    """Lifecycle states for a single communication (RN-15).

    Values:
        pendiente: Awaiting processing by worker.
        enviando: Currently being sent (worker has picked it up).
        enviado: Successfully sent via SMTP.
        error: Failed to send (may be retried if retry_count < max).
        cancelado: Cancelled by user before sending.
    """

    pendiente = "Pendiente"
    enviando = "Enviando"
    enviado = "Enviado"
    error = "Error"
    cancelado = "Cancelado"


class EstadoLote(str, enum.Enum):
    """Lifecycle states for a batch of communications (D-02).

    Values:
        pendiente: Batch created, awaiting processing or approval.
        aprobacion_pendiente: Requires admin approval before sending (RN-17).
        enviando: Currently being processed by worker.
        completado: All communications sent successfully.
        parcial: Some sent, some failed.
        cancelado: All communications cancelled (either by user or rejection).
    """

    pendiente = "Pendiente"
    aprobacion_pendiente = "AprobacionPendiente"
    enviando = "Enviando"
    completado = "Completado"
    parcial = "Parcial"
    cancelado = "Cancelado"


class LoteComunicacion(AppModel, TimestampMixin, TenantMixin):
    """A batch of bulk communications sent together.

    Tracks aggregated status across all individual communications in the batch.
    Per D-01, this model does NOT inherit AuditMixin.
    """

    __tablename__ = "lotes_comunicaciones"

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    materia_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materias.id", ondelete="CASCADE"),
        nullable=False,
    )
    enviado_por: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    asunto: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    total: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    enviados: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    fallidos: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=EstadoLote.pendiente.value,
    )
    requiere_aprobacion: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    aprobado_por: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    aprobado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    preview_confirmado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    def __repr__(self) -> str:
        return (
            f"<LoteComunicacion id={self.id} estado={self.estado} "
            f"total={self.total} enviados={self.enviados}>"
        )


class Comunicacion(AppModel, TimestampMixin, TenantMixin):
    """A single communication (email) addressed to one recipient.

    Per D-01, this model does NOT inherit AuditMixin.
    The ``destinatario`` field uses EncryptedString for PII protection (D-03).
    """

    __tablename__ = "comunicaciones"

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    lote_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("lotes_comunicaciones.id", ondelete="SET NULL"),
        nullable=True,
    )
    materia_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materias.id", ondelete="CASCADE"),
        nullable=False,
    )
    enviado_por: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    destinatario: Mapped[str] = mapped_column(
        EncryptedString,
        nullable=False,
    )
    asunto: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    cuerpo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EstadoComunicacion.pendiente.value,
    )
    error_msg: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    enviado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Comunicacion id={self.id} estado={self.estado} "
            f"destinatario=*** retry={self.retry_count}>"
        )
