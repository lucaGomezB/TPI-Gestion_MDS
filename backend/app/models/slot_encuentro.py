"""SlotEncuentro model — template for recurring encuentro instances.

A SlotEncuentro defines the recurrence pattern for encuentros:
regular weekly (dia_semana + cant_semanas) or a single date (fecha_unica).
Each slot generates N InstanciaEncuentro records eagerly.
"""

from datetime import date, time

from sqlalchemy import Date, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import AuditMixin, TenantMixin, TimestampMixin


class SlotEncuentro(AppModel, TimestampMixin, AuditMixin, TenantMixin):
    """Template defining recurrence for encuentros de una materia."""

    __tablename__ = "slots_encuentro"

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    asignacion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("asignaciones.id", ondelete="CASCADE"),
        nullable=False,
    )
    materia_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materias.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    titulo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    hora: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )
    dia_semana: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    fecha_inicio: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    cant_semanas: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    fecha_unica: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    meet_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    vig_desde: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    vig_hasta: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
