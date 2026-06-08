"""Pydantic schemas for Guardia management.

All schemas use ``extra='forbid'`` per project convention.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GuardiaCreate(BaseModel):
    """Create a new guardia record."""

    model_config = ConfigDict(extra="forbid")

    asignacion_id: str
    materia_id: str
    carrera_id: str
    cohorte_id: str
    dia: str = Field(..., min_length=2, max_length=10)
    horario: str = Field(..., min_length=1, max_length=50)
    estado: str | None = Field(None, pattern=r"^(Pendiente|Realizada|Cancelada)$")
    comentarios: str | None = None


class GuardiaResponse(BaseModel):
    """Guardia read response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    asignacion_id: str
    materia_id: str
    carrera_id: str
    cohorte_id: str
    dia: str
    horario: str
    estado: str
    comentarios: str | None = None
    creada_at: datetime
    created_at: datetime
    updated_at: datetime


class GuardiaListResponse(BaseModel):
    """Wrapper for paginated guardia list responses."""

    model_config = ConfigDict(extra="forbid")

    items: list[GuardiaResponse]
    total: int
