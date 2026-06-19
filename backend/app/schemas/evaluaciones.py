"""Pydantic schemas for FechaEvaluacion (evaluation dates / Calendario Evaluaciones).

All schemas use ``extra='forbid'`` per project convention.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class FechaEvaluacionCreate(BaseModel):
    """Create a new evaluation date. All fields required except auto-generated id."""

    model_config = ConfigDict(extra="forbid")

    materia_id: str
    cohorte_id: str
    tipo: str = Field(..., pattern=r"^(Parcial|TP|Coloquio)$")
    numero_instancia: int = Field(..., ge=1)
    fecha: date
    titulo: str = Field(..., min_length=1, max_length=200)


class FechaEvaluacionUpdate(BaseModel):
    """Partial update for an evaluation date. All fields optional."""

    model_config = ConfigDict(extra="forbid")

    materia_id: str | None = None
    cohorte_id: str | None = None
    tipo: str | None = Field(None, pattern=r"^(Parcial|TP|Coloquio)$")
    numero_instancia: int | None = Field(None, ge=1)
    fecha: date | None = None
    titulo: str | None = Field(None, min_length=1, max_length=200)


class FechaEvaluacionResponse(BaseModel):
    """Evaluation date read response — includes all fields."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    materia_id: str
    cohorte_id: str
    tipo: str
    numero_instancia: int
    fecha: date
    titulo: str
    created_at: datetime
    updated_at: datetime
