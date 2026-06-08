"""Pydantic schemas for encuentro management (SlotEncuentro / InstanciaEncuentro).

All schemas use ``extra='forbid'`` per project convention.
"""

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


# ── SlotEncuentro ────────────────────────────────────────────────────────────


class SlotEncuentroCreate(BaseModel):
    """Create a new recurring slot with eager instance generation."""

    model_config = ConfigDict(extra="forbid")

    asignacion_id: str
    materia_id: str
    titulo: str = Field(..., min_length=1, max_length=255)
    hora: time
    dia_semana: str = Field(..., min_length=2, max_length=10)
    fecha_inicio: date
    cant_semanas: int = Field(default=0, ge=0)
    fecha_unica: date | None = None
    meet_url: str | None = Field(None, max_length=500)
    vig_desde: date
    vig_hasta: date | None = None


class SlotEncuentroResponse(BaseModel):
    """SlotEncuentro read response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    asignacion_id: str
    materia_id: str
    titulo: str
    hora: time
    dia_semana: str
    fecha_inicio: date
    cant_semanas: int
    fecha_unica: date | None = None
    meet_url: str | None = None
    vig_desde: date
    vig_hasta: date | None = None
    estado: str
    created_at: datetime
    updated_at: datetime


# ── InstanciaEncuentro ───────────────────────────────────────────────────────


class InstanciaEncuentroCreate(BaseModel):
    """Create a single encuentro instance (without slot)."""

    model_config = ConfigDict(extra="forbid")

    materia_id: str
    fecha: date
    hora: time
    titulo: str = Field(..., min_length=1, max_length=255)
    meet_url: str | None = Field(None, max_length=500)


class InstanciaEncuentroUpdate(BaseModel):
    """Update an existing instance (estado, meet_url, video_url, comentario)."""

    model_config = ConfigDict(extra="forbid")

    estado: str | None = Field(None, pattern=r"^(Programado|Realizado|Cancelado)$")
    meet_url: str | None = Field(None, max_length=500)
    video_url: str | None = Field(None, max_length=500)
    comentario: str | None = None


class InstanciaEncuentroResponse(BaseModel):
    """InstanciaEncuentro read response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    slot_id: str | None = None
    materia_id: str
    fecha: date
    hora: time
    titulo: str
    estado: str
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Embed ────────────────────────────────────────────────────────────────────


class EmbedResponse(BaseModel):
    """HTML and Markdown snippet response for Moodle embedding."""

    model_config = ConfigDict(extra="forbid")

    html: str
    markdown: str
    total: int
