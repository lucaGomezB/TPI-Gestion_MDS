"""Pydantic schemas for audit log — requests, responses, and export.

All schemas use ``model_config = ConfigDict(extra='forbid')`` per project
convention to reject undeclared fields.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    """Response schema for a single audit log entry."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    fecha_hora: datetime
    actor_id: str
    impersonado_id: str | None = None
    materia_id: str | None = None
    accion: str
    detalle: dict[str, Any] | None = None
    filas_afectadas: int | None = None
    ip: str | None = None
    user_agent: str | None = None


class AuditLogSearchParams(BaseModel):
    """Query parameters for ``GET /api/admin/auditoria`` search."""

    model_config = ConfigDict(extra="forbid")

    q: str | None = Field(default=None, max_length=500)
    accion: str | None = Field(default=None, max_length=50)
    actor_id: str | None = None
    materia_id: str | None = None
    ip: str | None = Field(default=None, max_length=45)
    fecha_desde: datetime | None = None
    fecha_hasta: datetime | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class AuditLogSearchResponse(BaseModel):
    """Paginated response for audit log search."""

    model_config = ConfigDict(extra="forbid")

    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


class DocenteInteraccionesResponse(BaseModel):
    """Aggregated interaction metrics for a teacher (F9.1)."""

    model_config = ConfigDict(extra="forbid")

    docente_id: str
    total_acciones: int
    por_accion: dict[str, int]
    por_materia: list[dict[str, Any]]
    ultimas_acciones: list[AuditLogResponse]


class AuditExportParams(BaseModel):
    """Query parameters for ``GET /api/admin/auditoria/exportar``."""

    model_config = ConfigDict(extra="forbid")

    q: str | None = Field(default=None, max_length=500)
    accion: str | None = Field(default=None, max_length=50)
    actor_id: str | None = None
    materia_id: str | None = None
    ip: str | None = Field(default=None, max_length=45)
    fecha_desde: datetime | None = None
    fecha_hasta: datetime | None = None
    formato: str = Field(default="csv", pattern=r"^(csv|json)$")
