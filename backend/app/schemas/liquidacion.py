"""Pydantic schemas for liquidaciones (C-19).

All schemas have ``extra='forbid'`` to reject undeclared fields.
Schemas cover:
- LiquidacionCreate (internal create)
- LiquidacionResponse / LiquidacionDetailResponse (API responses)
- LiquidacionKPI (aggregation)
- LiquidacionListResponse (paginated list with KPIs)
"""

from typing import Any

from pydantic import ConfigDict, Field
from pydantic import BaseModel as PydanticBaseModel


class _ExtraForbid(PydanticBaseModel):
    """Base schema with from_attributes=True and extra='forbid'."""

    model_config: ConfigDict = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


# ── Create schema (internal) ─────────────────────────────────────────────


class LiquidacionCreate(_ExtraForbid):
    """Schema for creating a new Liquidacion record.

    Used internally by LiquidacionService when calculating settlements.
    """

    cohorte_id: str
    periodo: str = Field(
        ...,
        min_length=7,
        max_length=7,
        description="Period in YYYY-MM format",
    )
    usuario_id: str
    rol: str
    comisiones: list[str] = Field(default_factory=list)
    monto_base: float
    monto_plus: float
    total: float
    es_nexo: bool = False
    excluido_por_factura: bool = False


# ── Response schemas ─────────────────────────────────────────────────────


class LiquidacionResponse(_ExtraForbid):
    """Schema for a single liquidacion in list/detail responses."""

    id: str
    tenant_id: str
    cohorte_id: str
    periodo: str
    usuario_id: str
    rol: str
    comisiones: list[str]
    monto_base: float
    monto_plus: float
    total: float
    es_nexo: bool
    excluido_por_factura: bool
    estado: str
    created_at: str
    cerrada_at: str | None = None


class LiquidacionDetailResponse(LiquidacionResponse):
    """Extended response with desglose (breakdown) fields.

    Includes:
    - desglose_base: info about the vigente SalarioBase used
    - desglose_plus: list of each SalarioPlus applied
    """

    desglose_base: dict[str, Any] = Field(
        default_factory=dict,
        description="Breakdown of the base salary used",
    )
    desglose_plus: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Breakdown of each plus amount applied",
    )


# ── KPI schema ────────────────────────────────────────────────────────────


class LiquidacionKPI(_ExtraForbid):
    """KPI aggregation per RN-38."""

    total_sin_factura: float = 0.0
    total_con_factura: float = 0.0
    total_general: float = 0.0


# ── List response ─────────────────────────────────────────────────────────


class LiquidacionListResponse(_ExtraForbid):
    """Paginated list response with KPI headers."""

    items: list[LiquidacionResponse]
    kpis: LiquidacionKPI
    total: int
    page: int
    page_size: int
