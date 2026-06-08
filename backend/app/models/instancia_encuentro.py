"""InstanciaEncuentro model — concrete encuentro occurrence.

Each InstanciaEncuentro is a specific encuentro session with its own
state independent of the SlotEncuentro that generated it (RN-14).
Instancias can exist without a slot (slot_id=null) for extraordinary sessions.
"""

from datetime import date, time

from sqlalchemy import Date, ForeignKey, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import AuditMixin, TenantMixin, TimestampMixin


class InstanciaEncuentro(AppModel, TimestampMixin, AuditMixin, TenantMixin):
    """A concrete encuentro session with independent state."""

    __tablename__ = "instancias_encuentro"

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    slot_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("slots_encuentro.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    materia_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materias.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fecha: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    hora: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        default="Programado",
        nullable=False,
    )
    meet_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    video_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    comentario: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
