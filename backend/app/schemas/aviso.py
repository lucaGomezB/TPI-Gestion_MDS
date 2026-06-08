"""Pydantic schemas for avisos (C-12).

All schemas use extra='forbid' per project convention.

Schemas:
- AlcanceAviso, SeveridadAviso: Enums for alcance and severidad.
- AvisoCreate: Admin creates a new aviso with alcance-contexto validation.
- AvisoUpdate: Admin updates an existing aviso (partial).
- AvisoResponse: Full aviso data returned to client.
- AvisoListResponse: Paginated list of avisos.
- AckResponse: Acknowledgment confirmation response.
"""

import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AlcanceAviso(str, enum.Enum):
    """Scope of aviso visibility (RN-20)."""

    GLOBAL = "Global"
    POR_MATERIA = "PorMateria"
    POR_COHORTE = "PorCohorte"
    POR_ROL = "PorRol"


class SeveridadAviso(str, enum.Enum):
    """Severity level for an aviso."""

    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"
    CRITICO = "Critico"


# ── Create schema ──────────────────────────────────────────────────────


class AvisoCreate(BaseModel):
    """Schema for creating a new aviso (admin)."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    titulo: str = Field(..., min_length=1, max_length=255)
    cuerpo: str = Field(..., min_length=1)
    alcance: AlcanceAviso
    materia_id: str | None = None
    cohorte_id: str | None = None
    rol_destino: str | None = None
    severidad: SeveridadAviso
    inicio_en: datetime
    fin_en: datetime
    orden: int = Field(default=0, ge=0)
    activo: bool = True
    requiere_ack: bool = False

    @model_validator(mode="after")
    def _validate_alcance_context(self) -> "AvisoCreate":
        """Validate that context fields are present based on alcance."""
        if self.alcance == AlcanceAviso.POR_MATERIA and not self.materia_id:
            raise ValueError("materia_id es requerido cuando alcance es PorMateria")
        if self.alcance == AlcanceAviso.POR_COHORTE and not self.cohorte_id:
            raise ValueError("cohorte_id es requerido cuando alcance es PorCohorte")
        if self.alcance == AlcanceAviso.POR_ROL and not self.rol_destino:
            raise ValueError("rol_destino es requerido cuando alcance es PorRol")
        return self

    @model_validator(mode="after")
    def _validate_vigencia(self) -> "AvisoCreate":
        """Validate that inicio_en is before fin_en (RN-18)."""
        if self.inicio_en >= self.fin_en:
            raise ValueError("inicio_en debe ser anterior a fin_en")
        return self


# ── Update schema ──────────────────────────────────────────────────────


class AvisoUpdate(BaseModel):
    """Schema for updating an existing aviso (admin, partial)."""

    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(None, min_length=1, max_length=255)
    cuerpo: str | None = Field(None, min_length=1)
    alcance: AlcanceAviso | None = None
    materia_id: str | None = None
    cohorte_id: str | None = None
    rol_destino: str | None = None
    severidad: SeveridadAviso | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = Field(None, ge=0)
    activo: bool | None = None
    requiere_ack: bool | None = None


# ── Response schemas ───────────────────────────────────────────────────


class AvisoResponse(BaseModel):
    """Full aviso data returned to clients."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    alcance: str
    materia_id: str | None = None
    cohorte_id: str | None = None
    rol_destino: str | None = None
    severidad: str
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    created_at: datetime
    updated_at: datetime
    ack_count: int = 0


class AvisoListResponse(BaseModel):
    """Paginated list of avisos."""

    model_config = ConfigDict(extra="forbid")

    items: list[AvisoResponse]
    total: int


# ── Acknowledgment schema ──────────────────────────────────────────────


class AckResponse(BaseModel):
    """Response for acknowledgment confirmation (RN-19)."""

    model_config = ConfigDict(extra="forbid")

    acknowledged: bool
    leido_en: datetime
