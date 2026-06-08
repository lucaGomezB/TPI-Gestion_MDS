"""ReservaColoquio model — student reservation for a coloquio turn on a specific day.

Each reservation links a student (alumno) to a coloquio evaluacion on a specific day.
Unique constraint on (evaluacion_id, alumno_id) ensures one reservation per student
per convocatoria.
"""

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin


class ReservaColoquio(AppModel, TimestampMixin, TenantMixin):
    """A student's reservation of a coloquio turn on a specific day."""

    __tablename__ = "reservas_coloquio"

    __table_args__ = (
        UniqueConstraint(
            "evaluacion_id",
            "alumno_id",
            name="uq_reserva_coloquio_eval_alumno",
        ),
        Index(
            "ix_reserva_coloquio_evaluacion",
            "evaluacion_id",
        ),
        Index(
            "ix_reserva_coloquio_alumno",
            "alumno_id",
        ),
    )

    # ── Override TenantMixin.tenant_id to be non-nullable ────────────
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    evaluacion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("evaluaciones_coloquio.id", ondelete="CASCADE"),
        nullable=False,
    )
    alumno_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    dia: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    confirmada: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    def __repr__(self) -> str:
        return (
            f"<ReservaColoquio(id={self.id}, evaluacion_id={self.evaluacion_id}, "
            f"alumno_id={self.alumno_id}, dia={self.dia})>"
        )
