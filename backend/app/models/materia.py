"""Materia model — subject catalog within a tenant.

A materia is a unique definition in the subject catalog — not tied to a
specific carrera or cohorte. Each tenant has its own catalog of materias
with unique subject codes.
"""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import AuditMixin, EstadoAcademico, TenantMixin, TimestampMixin


class Materia(AppModel, TimestampMixin, AuditMixin, TenantMixin):
    """A subject in the tenant-wide academic catalog."""

    __tablename__ = "materias"

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_materia_tenant_codigo"),
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
