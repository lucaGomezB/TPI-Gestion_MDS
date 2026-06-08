"""Cohorte model — cohort within a carrera.

A cohort represents a group of students that start a program together
(e.g., "MAR-2025", "AGO-2026"). Cohorts have temporal validity dates
and belong to exactly one carrera.
"""

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import AuditMixin, EstadoAcademico, TenantMixin, TimestampMixin


class Cohorte(AppModel, TimestampMixin, AuditMixin, TenantMixin):
    """A cohort (admission group) within a carrera."""

    __tablename__ = "cohortes"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "carrera_id", "nombre", name="uq_cohorte_tenant_carrera_nombre"
        ),
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    carrera_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("carreras.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    anio: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    vig_desde: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    vig_hasta: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    estado: Mapped[EstadoAcademico] = mapped_column(
        String(20),
        default=EstadoAcademico.ACTIVA,
        nullable=False,
    )
