"""Pydantic schemas for team management (C-05).

All schemas use ``extra='forbid'`` per project convention.

Schemas:
- AsignacionCreate, AsignacionUpdate, AsignacionResponse — individual CRUD
- AsignacionMasivaRequest, AsignacionMasivaResponse — bulk assignment
- ClonarRequest, ClonarResponse — clone operation
- VigenciaRequest, VigenciaResponse — bulk vigencia update
- EquipoExportRow — export row representation
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.types import RolDocente


# ── Individual CRUD schemas ──────────────────────────────────────────────


class AsignacionCreate(BaseModel):
    """Create a new assignment linking a user to a role in an academic context."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    usuario_id: str
    rol: RolDocente
    materia_id: Optional[str] = None
    carrera_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    comisiones: list[str] = Field(default_factory=list)
    responsable_id: Optional[str] = None
    vig_desde: date
    vig_hasta: Optional[date] = None

    @model_validator(mode="after")
    def _validate_date_range(self) -> "AsignacionCreate":
        """Validate vig_desde <= vig_hasta if vig_hasta provided."""
        if self.vig_hasta is not None and self.vig_desde > self.vig_hasta:
            raise ValueError("vig_desde must be on or before vig_hasta")
        return self

    @model_validator(mode="after")
    def _validate_rol_context(self) -> "AsignacionCreate":
        """PROFESOR and TUTOR require materia_id."""
        rol_value = self.rol.value if hasattr(self.rol, "value") else str(self.rol)
        if rol_value in ("PROFESOR", "TUTOR") and not self.materia_id:
            raise ValueError(
                f"rol '{rol_value}' requires materia_id (academic context)"
            )
        return self


class AsignacionUpdate(BaseModel):
    """Partial update for an existing assignment."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    rol: Optional[RolDocente] = None
    materia_id: Optional[str] = None
    carrera_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    comisiones: Optional[list[str]] = None
    responsable_id: Optional[str] = None
    vig_desde: Optional[date] = None
    vig_hasta: Optional[date] = None

    @model_validator(mode="after")
    def _validate_date_range(self) -> "AsignacionUpdate":
        """Validate vig_desde <= vig_hasta if both provided."""
        if self.vig_desde is not None and self.vig_hasta is not None:
            if self.vig_desde > self.vig_hasta:
                raise ValueError("vig_desde must be on or before vig_hasta")
        return self


class AsignacionResponse(BaseModel):
    """Asignacion read response with computed estado_vigencia."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    usuario_id: str
    rol: str
    materia_id: Optional[str] = None
    carrera_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    comisiones: list[str]
    responsable_id: Optional[str] = None
    vig_desde: date
    vig_hasta: Optional[date] = None
    estado_vigencia: str
    created_at: datetime
    updated_at: datetime


# ── Bulk assignment schemas ──────────────────────────────────────────────


class AsignacionMasivaRequest(BaseModel):
    """Bulk assign multiple usuarios to the same academic context."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    usuario_ids: list[str] = Field(..., min_length=1)
    rol: RolDocente
    materia_id: Optional[str] = None
    carrera_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    comisiones: list[str] = Field(default_factory=list)
    responsable_id: Optional[str] = None
    vig_desde: date
    vig_hasta: Optional[date] = None

    @model_validator(mode="after")
    def _validate_date_range(self) -> "AsignacionMasivaRequest":
        """Validate vig_desde <= vig_hasta if vig_hasta provided."""
        if self.vig_hasta is not None and self.vig_desde > self.vig_hasta:
            raise ValueError("vig_desde must be on or before vig_hasta")
        return self

    @model_validator(mode="after")
    def _validate_rol_context(self) -> "AsignacionMasivaRequest":
        """PROFESOR and TUTOR require materia_id."""
        rol_value = self.rol.value if hasattr(self.rol, "value") else str(self.rol)
        if rol_value in ("PROFESOR", "TUTOR") and not self.materia_id:
            raise ValueError(
                f"rol '{rol_value}' requires materia_id (academic context)"
            )
        return self


class AsignacionMasivaResponse(BaseModel):
    """Response after bulk assignment."""

    model_config = ConfigDict(extra="forbid")

    creadas: list[AsignacionResponse]
    total: int


# ── Clone schemas ────────────────────────────────────────────────────────


class ClonarRequest(BaseModel):
    """Clone all Vigente assignments from a source context to a destination."""

    model_config = ConfigDict(extra="forbid")

    origen_materia_id: str
    origen_carrera_id: str
    origen_cohorte_id: str
    destino_materia_id: str
    destino_carrera_id: str
    destino_cohorte_id: str

    @model_validator(mode="after")
    def _validate_different_contexts(self) -> "ClonarRequest":
        """Source and destination must differ (no self-clone)."""
        if (
            self.origen_materia_id == self.destino_materia_id
            and self.origen_carrera_id == self.destino_carrera_id
            and self.origen_cohorte_id == self.destino_cohorte_id
        ):
            raise ValueError("Source and destination must differ")
        return self


class ClonarResponse(BaseModel):
    """Response after clone operation."""

    model_config = ConfigDict(extra="forbid")

    clonadas: int


# ── Bulk vigencia schemas ────────────────────────────────────────────────


class VigenciaRequest(BaseModel):
    """Bulk update vigencia dates for all assignments matching the academic context."""

    model_config = ConfigDict(extra="forbid")

    materia_id: Optional[str] = None
    carrera_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    vig_desde: date
    vig_hasta: Optional[date] = None

    @model_validator(mode="after")
    def _validate_date_range(self) -> "VigenciaRequest":
        """Validate vig_desde <= vig_hasta if vig_hasta provided."""
        if self.vig_hasta is not None and self.vig_desde > self.vig_hasta:
            raise ValueError("vig_desde must be on or before vig_hasta")
        return self


class VigenciaResponse(BaseModel):
    """Response after bulk vigencia update."""

    model_config = ConfigDict(extra="forbid")

    actualizadas: int


# ── Export schema ────────────────────────────────────────────────────────


class EquipoExportRow(BaseModel):
    """A single row in the CSV export for a teaching team."""

    model_config = ConfigDict(extra="forbid")

    docente_nombre: str
    docente_apellidos: str
    docente_email: str
    rol: str
    comisiones: str
    responsable_nombre: str
    vig_desde: date
    vig_hasta: Optional[date] = None
    estado_vigencia: str
