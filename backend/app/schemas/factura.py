"""Pydantic schemas for facturas (C-20).

All schemas have ``extra='forbid'`` to reject undeclared fields.
Schemas cover:
- FacturaCreate (internal create)
- FacturaResponse / FacturaDetailResponse (API responses)
- FacturaListResponse (paginated list)
"""

from __future__ import annotations

import enum

from pydantic import ConfigDict, Field
from pydantic import BaseModel as PydanticBaseModel


class EstadoFactura(str, enum.Enum):
    """Factura lifecycle state matching the model enum."""

    PENDIENTE = "Pendiente"
    ABONADA = "Abonada"


class _ExtraForbid(PydanticBaseModel):
    """Base schema with from_attributes=True and extra='forbid'."""

    model_config: ConfigDict = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


# ── Create schema (internal) ─────────────────────────────────────────────


class FacturaCreate(_ExtraForbid):
    """Schema for creating a new Factura record.

    Used internally by FacturaService when uploading invoices.
    """

    usuario_id: str
    periodo: str = Field(
        ...,
        min_length=7,
        max_length=7,
        pattern=r"^\d{4}-\d{2}$",
        description="Period in YYYY-MM format",
    )
    detalle: str = Field(
        ...,
        max_length=500,
    )
    referencia_archivo: str = Field(
        ...,
        max_length=500,
    )
    tamano_kb: float = Field(
        ...,
        ge=0,
        description="File size in kilobytes",
    )


# ── Response schemas ─────────────────────────────────────────────────────


class FacturaResponse(_ExtraForbid):
    """Schema for a single factura in list/detail responses."""

    id: str
    tenant_id: str
    usuario_id: str
    periodo: str
    detalle: str
    referencia_archivo: str
    tamano_kb: float
    estado: str
    cargada_at: str
    abonada_at: str | None = None


class FacturaDetailResponse(FacturaResponse):
    """Extended response with download URL.

    Includes:
    - descargar_url: URL to download the PDF file.
    """

    descargar_url: str | None = Field(
        default=None,
        description="URL to download the PDF file",
    )


# ── List response ─────────────────────────────────────────────────────────


class FacturaListResponse(_ExtraForbid):
    """Paginated list response."""

    items: list[FacturaResponse]
    total: int
    page: int
    page_size: int
