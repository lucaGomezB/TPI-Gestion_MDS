"""FechaEvaluacion model — scheduled evaluation dates.

Each record represents a scheduled evaluation (Parcial, TP, Coloquio)
within a materia and cohorte scope, uniquely identified by the combination
of tenant, materia, cohorte, tipo, and numero_instancia.
"""

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import AuditMixin, TenantMixin, TimestampMixin


class FechaEvaluacion(AppModel, TimestampMixin, AuditMixin, TenantMixin):
    """Scheduled evaluation date for a materia within a cohorte.

    Types: ``Parcial``, ``TP``, ``Coloquio``.
    Soft-deletable via AuditMixin (estado = Inactivo).
    """

    __tablename__ = "fechas_evaluacion"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "materia_id",
            "cohorte_id",
            "tipo",
            "numero_instancia",
            name="uq_fecha_eval_tenant_mat_cohorte_tipo_inst",
        ),
    )

    # ── Override TenantMixin.tenant_id to be non-nullable ──────────────
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

    cohorte_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("cohortes.id", ondelete="CASCADE"),
        nullable=False,
    )

    tipo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    numero_instancia: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    fecha: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    titulo: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<FechaEvaluacion(id={self.id}, tipo={self.tipo}, "
            f"numero_instancia={self.numero_instancia}, fecha={self.fecha})>"
        )
