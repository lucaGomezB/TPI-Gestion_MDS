"""EvaluacionColoquio model — coloquio convocatoria with configurable days and quotas.

Each evaluacion represents a coloquio call for a materia, with a JSONB ``dias``
field containing individual day configurations (date, cupos, reservados).
"""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin


class EvaluacionColoquio(AppModel, TimestampMixin, TenantMixin):
    """A coloquio convocatoria (evaluation call) with configurable days and quotas."""

    __tablename__ = "evaluaciones_coloquio"

    __table_args__ = (
        Index(
            "ix_eval_coloquio_tenant_materia",
            "tenant_id",
            "materia_id",
        ),
    )

    # ── Override TenantMixin.tenant_id to be non-nullable ────────────
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
    titulo: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    dias: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=[],
    )
    creado_por: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    activa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    # Store cohorte_id for cross-reference (nullable for future use)
    cohorte_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("cohortes.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<EvaluacionColoquio(id={self.id}, titulo={self.titulo}, activa={self.activa})>"
