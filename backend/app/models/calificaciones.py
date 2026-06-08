"""Calificacion and UmbralMateria models — grades and approval thresholds.

Calificacion links a student (via EntradaPadron) to a grade on an evaluable
activity within a subject. UmbralMateria stores configurable approval
thresholds per (asignacion x materia) pair.

Design decisions (per C-07 design.md):
- D4: ``aprobado`` is derived at import time in the service layer, not in DB.
- D9: Calificacion references the student via ``entrada_padron_id`` (FK),
      not a direct ``usuario_id``.
- No AuditMixin — grade records are immutable once created (only mass-delete
  is supported via DELETE endpoint, not individual updates).
- ``origen`` is a simple string field (no enum type at DB level) — validated
  at the Pydantic schema layer.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin


class Calificacion(AppModel, TimestampMixin, TenantMixin):
    """A grade or evaluation status for a student on an activity.

    Each record represents one student's result on one evaluable activity.
    The ``aprobado`` field is computed at import time by the service layer
    based on configured thresholds.

    Attributes:
        id: Auto-generated UUID primary key.
        tenant_id: FK to tenants.id (non-nullable override).
        entrada_padron_id: FK to entradas_padron.id (CASCADE).
        materia_id: FK to materias.id (CASCADE).
        actividad: Name of the evaluable activity (e.g. "TP 1").
        nota_numerica: Numeric grade (0.00-100.00), nullable.
        nota_textual: Qualitative grade text (e.g. "Satisfactorio"), nullable.
        aprobado: Whether the student passed this activity.
        origen: Source of the grade — "Importado" or "Manual".
        cargado_por: FK to usuarios.id — who imported/created this record.
        importado_at: Timestamp when the grade was imported.
    """

    __tablename__ = "calificaciones"

    __table_args__ = (
        # Composite index for scope-isolated DELETE by (materia_id, cargado_por)
        # Composite index for listing by (materia_id, actividad)
    )

    # ── Override TenantMixin.tenant_id to be non-nullable ────────────
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    entrada_padron_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("entradas_padron.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    materia_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materias.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actividad: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    nota_numerica: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    nota_textual: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    aprobado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    origen: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Importado",
    )
    cargado_por: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    importado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────────
    entrada_padron: Mapped["EntradaPadron"] = relationship(  # type: ignore[name-defined] # noqa: F821
        "EntradaPadron",
        back_populates="calificaciones",
        lazy="selectin",
    )
    materia: Mapped["Materia"] = relationship(  # type: ignore[name-defined] # noqa: F821
        "Materia",
        lazy="selectin",
    )


class UmbralMateria(AppModel, TimestampMixin, TenantMixin):
    """Approval threshold configuration for a (asignacion x materia) pair.

    Each PROFESOR can configure their own threshold for a materia via their
    Asignacion. If no UmbralMateria exists, defaults are used (60% threshold,
    ["Satisfactorio", "Supera lo esperado"] for textual grades).

    Attributes:
        id: Auto-generated UUID primary key.
        tenant_id: FK to tenants.id (non-nullable override).
        asignacion_id: FK to asignaciones.id (CASCADE).
        materia_id: FK to materias.id (CASCADE).
        umbral_pct: Percentage threshold (0-100, default 60).
        valores_aprobatorios: JSONB list of approved textual values.
    """

    __tablename__ = "umbrales_materia"

    # ── Override TenantMixin.tenant_id to be non-nullable ────────────
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
    umbral_pct: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
    )
    valores_aprobatorios: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: ["Satisfactorio", "Supera lo esperado"],
    )

    # ── Relationships ────────────────────────────────────────────────
    materia: Mapped["Materia"] = relationship(  # type: ignore[name-defined] # noqa: F821
        "Materia",
        lazy="selectin",
    )
