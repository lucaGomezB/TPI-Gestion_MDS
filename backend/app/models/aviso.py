"""Aviso model — system notice board (tablon de avisos).

Implements entity E13 as defined in the data model. An aviso is a
time-scoped notice with configurable alcance, severidad, and optional
acknowledgment requirement.

Per D-01 in design.md, this model uses an explicit ``activo`` flag
instead of ``AuditMixin`` because the lifecycle is driven by vigencia
(inicio_en / fin_en), not by soft-delete.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin


class Aviso(AppModel, TimestampMixin, TenantMixin):
    """A system notice visible to users based on alcance, vigencia, and rol.

    Attributes:
        id: UUID primary key.
        tenant_id: Tenant scope (FK to tenants).
        alcance: Scope of visibility — Global, PorMateria, PorCohorte, PorRol.
        materia_id: Optional materia context for PorMateria alcance.
        cohorte_id: Optional cohorte context for PorCohorte alcance.
        rol_destino: Optional target role for PorRol alcance.
        severidad: Severity level — Baja, Media, Alta, Critico.
        titulo: Short notice title.
        cuerpo: Full notice body text.
        inicio_en: Start of visibility window (RN-18).
        fin_en: End of visibility window (RN-18).
        orden: Display priority (lower = higher priority).
        activo: Manual active/inactive flag.
        requiere_ack: Whether acknowledgment is required (RN-19).
    """

    __tablename__ = "avisos"

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    alcance: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    materia_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materias.id", ondelete="CASCADE"),
        nullable=True,
    )
    cohorte_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("cohortes.id", ondelete="CASCADE"),
        nullable=True,
    )
    rol_destino: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    severidad: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    cuerpo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    inicio_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    fin_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    orden: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    requiere_ack: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Aviso id={self.id} alcance={self.alcance} "
            f"severidad={self.severidad} activo={self.activo}>"
        )
