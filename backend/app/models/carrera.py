"""Carrera model — academic program within a tenant.

Each tenant has its own catalog of carreras with unique program codes.
A carrera represents an academic program (e.g., "Tecnicatura Universitaria
en Programación y Análisis de Datos") with a short unique code (e.g., "TUPAD").
"""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import AuditMixin, EstadoAcademico, TenantMixin, TimestampMixin


class Carrera(AppModel, TimestampMixin, AuditMixin, TenantMixin):
    """An academic program offered by the institution."""

    __tablename__ = "carreras"

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_carrera_tenant_codigo"),
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    codigo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    estado: Mapped[EstadoAcademico] = mapped_column(
        String(20),
        default=EstadoAcademico.ACTIVA,
        nullable=False,
    )
