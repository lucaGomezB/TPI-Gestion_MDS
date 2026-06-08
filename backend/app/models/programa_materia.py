"""ProgramaMateria model — syllabus document registry.

Links an official syllabus document (PDF) to a specific materia + carrera + cohorte
combination. This is an informational document registry without soft-delete support.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TenantMixin


class ProgramaMateria(AppModel, TenantMixin):
    """An official syllabus document for a subject in a specific career+cohort context.

    No AuditMixin — hard delete only. ``cargado_at`` replaces ``created_at``.
    """

    __tablename__ = "programas_materia"

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
    carrera_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("carreras.id", ondelete="CASCADE"),
        nullable=False,
    )
    cohorte_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("cohortes.id", ondelete="CASCADE"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    referencia_archivo: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    cargado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
