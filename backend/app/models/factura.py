"""Factura model — teacher invoice registry (E20).

A Factura represents a monthly invoice uploaded by a monotributista teacher
(facturador=true). It lives independently of the liquidacion system per RN-35.

Design decisions (per C-20 design.md):
- D-03: Custom ``estado`` field (Pendiente/Abonada) — does not use AuditMixin.
- D-01: One row per (usuario, periodo) — one invoice per teacher per month.
"""

from __future__ import annotations

import enum
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel


class EstadoFactura(str, enum.Enum):
    """Lifecycle state for a factura (D-03: custom estado).

    Only two states per RN-39: Pendiente (pending) and Abonada (paid).
    No cancelled or rejected states.
    """

    PENDIENTE = "Pendiente"
    ABONADA = "Abonada"


class Factura(AppModel):
    """A single teacher's monthly invoice (E20)."""

    __tablename__ = "facturas"

    __table_args__ = (
        Index(
            "ix_facturas_tenant_periodo",
            "tenant_id", "periodo",
        ),
        Index(
            "ix_facturas_usuario_id",
            "usuario_id",
        ),
        Index(
            "ix_facturas_tenant_estado",
            "tenant_id", "estado",
        ),
    )

    # ── FK columns ────────────────────────────────────────────────────
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
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

    detalle: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    referencia_archivo: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    tamano_kb: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.0,
        server_default=sa.text("0"),
    )

    # ── State machine (D-03) ──────────────────────────────────────────
    estado: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=EstadoFactura.PENDIENTE.value,
        server_default=sa.text(f"'{EstadoFactura.PENDIENTE.value}'"),
    )

    # ── Timestamps ────────────────────────────────────────────────────
    cargada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    abonada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
