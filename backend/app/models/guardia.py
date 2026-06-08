"""Guardia model — record of a docente's duty/office hours.

A Guardia is an independent entity representing scheduled attention hours
for a docente within an academic context. It has its own semantics separate
from encuentros: no meet_url, no instance generation, no embed snippets.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin


class Guardia(AppModel, TimestampMixin, TenantMixin):
    """Record of a docente's scheduled duty/office hours.

    Per design D-04, Guardia is separate from InstanciaEncuentro.
    No AuditMixin — Guardia uses its own estado field (Pendiente/Realizada/Cancelada).
    """

    __tablename__ = "guardias"

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
    dia: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    horario: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        default="Pendiente",
        nullable=False,
    )
    comentarios: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    creada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
