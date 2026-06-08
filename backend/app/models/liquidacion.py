"""Liquidacion model — monthly teacher salary settlement (E19).

A Liquidacion represents a single teacher's salary settlement for a
given (cohorte, mes) pair. It persists the snapshot of settlement data
at the time of calculation, not live upstream references.

Design decisions (per C-19 design.md):
- D-01: One row per (cohorte, mes, docente) for granularity.
- D-03: Custom ``estado`` field (Abierta/Cerrada) — does not use AuditMixin.
- D-05: Calculation is on-demand, not pre-cached.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel


class EstadoLiquidacion(str, enum.Enum):
    """Lifecycle state for a liquidacion (D-03: custom estado)."""

    ABIERTA = "Abierta"
    CERRADA = "Cerrada"


class Liquidacion(AppModel):
    """A single teacher's salary settlement for a (cohorte, mes) pair (E19)."""

    __tablename__ = "liquidaciones"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "cohorte_id", "usuario_id", "periodo",
            name="uq_liquidacion_cohorte_usuario_periodo",
        ),
        Index(
            "ix_liquidaciones_periodo",
            "tenant_id", "periodo",
        ),
        Index(
            "ix_liquidaciones_cohorte_periodo",
            "tenant_id", "cohorte_id", "periodo",
        ),
        Index(
            "ix_liquidaciones_usuario_id",
            "usuario_id",
        ),
        Index(
            "ix_liquidaciones_estado",
            "tenant_id", "estado",
        ),
    )

    # ── FK columns ────────────────────────────────────────────────────
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    cohorte_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("cohortes.id", ondelete="CASCADE"),
        nullable=False,
    )
    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Domain fields ─────────────────────────────────────────────────
    periodo: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
    )  # YYYY-MM

    rol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    comisiones: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    monto_base: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    monto_plus: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    total: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    es_nexo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    excluido_por_factura: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # ── State machine (D-03) ──────────────────────────────────────────
    estado: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=EstadoLiquidacion.ABIERTA.value,
    )

    # ── Timestamps ────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    cerrada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
