"""Tarea (E12) and ComentarioTarea models for internal task tracking.

Tarea represents an internal task assigned between teaching or
coordination staff. Each task has a traceable lifecycle with explicit
state transitions: Pendiente -> En progreso -> Resuelta, with
Cancelada allowed from any state.

ComentarioTarea represents an immutable comment on a task, authored
by a user at a specific timestamp.
"""

import enum

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin


class EstadoTarea(str, enum.Enum):
    """Enum representing the lifecycle state of a Tarea.

    Values follow forward-only progression:
    Pendiente -> En progreso -> Resuelta (normal flow)
    Cancelada -> allowed from any state (emergency exit)
    """

    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    RESUELTA = "Resuelta"
    CANCELADA = "Cancelada"


class Tarea(AppModel, TimestampMixin, TenantMixin):
    """An internal task assigned between staff members.

    Each task has a clear asignador->asignado direction, optional
    materia context, and an estado lifecycle with forward-only
    transitions.
    """

    __tablename__ = "tareas"

    materia_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materias.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    asignado_a: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asignado_por: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        default=EstadoTarea.PENDIENTE.value,
        nullable=False,
    )
    descripcion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    contexto_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────────

    tenant = relationship("Tenant", lazy="joined")
    materia = relationship("Materia", lazy="joined")
    asignado_a_usuario = relationship(
        "Usuario",
        foreign_keys=[asignado_a],
        lazy="joined",
    )
    asignado_por_usuario = relationship(
        "Usuario",
        foreign_keys=[asignado_por],
        lazy="joined",
    )
    comentarios = relationship(
        "ComentarioTarea",
        back_populates="tarea",
        lazy="selectin",
        order_by="ComentarioTarea.created_at",
    )

    # ── Indexes ─────────────────────────────────────────────────────────

    __table_args__ = (
        Index("ix_tareas_tenant_estado", "tenant_id", "estado"),
    )


class ComentarioTarea(AppModel, TimestampMixin, TenantMixin):
    """An immutable comment on a Tarea, authored by a user.

    Comments are append-only: once created, they cannot be edited
    or deleted. This ensures full auditability of task discussions.

    Uses ``created_at`` from TimestampMixin for the comment timestamp.
    ``updated_at`` is inherited but semantically irrelevant for immutable
    comments.
    """

    __tablename__ = "comentarios_tarea"

    tarea_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tareas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    autor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    texto: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────

    tarea = relationship("Tarea", back_populates="comentarios", lazy="joined")
    autor = relationship("Usuario", foreign_keys=[autor_id], lazy="joined")
