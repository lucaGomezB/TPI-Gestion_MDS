"""ResultadoColoquio model — student grade/result for a coloquio evaluation.

Each result records a student's grade and approval status for a coloquio.
Unique constraint on (evaluacion_id, alumno_id) ensures one result per student
per convocatoria.
"""

from sqlalchemy import Boolean, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin


class ResultadoColoquio(AppModel, TimestampMixin, TenantMixin):
    """A student's grade/result for a coloquio evaluation."""

    __tablename__ = "resultados_coloquio"

    __table_args__ = (
        UniqueConstraint(
            "evaluacion_id",
            "alumno_id",
            name="uq_resultado_coloquio_eval_alumno",
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
    nota: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    aprobado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    registrado_por: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ResultadoColoquio(id={self.id}, evaluacion_id={self.evaluacion_id}, "
            f"alumno_id={self.alumno_id}, nota={self.nota})>"
        )
