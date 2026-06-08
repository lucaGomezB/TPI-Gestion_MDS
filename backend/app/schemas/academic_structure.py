"""Pydantic schemas for academic structure CRUD.

All schemas use ``extra='forbid'`` per project convention.

Schemas:
- CarreraCreate, CarreraUpdate, CarreraResponse
- CohorteCreate, CohorteUpdate, CohorteResponse
- MateriaCreate, MateriaUpdate, MateriaResponse
- ProgramaMateriaResponse, ProgramaMateriaUploadResponse
"""

import re
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _validate_codigo(value: str) -> str:
    """Uppercase and validate codigo format.

    Args:
        value: The raw codigo string.

    Returns:
        Uppercased codigo.

    Raises:
        ValueError: If codigo contains invalid characters.
    """
    uppered = value.upper()
    if not re.match(r"^[A-Z0-9_]{1,20}$", uppered):
        raise ValueError(
            "codigo must be 1-20 uppercase alphanumeric characters "
            "with underscores only"
        )
    return uppered


# ── Carrera schemas ──────────────────────────────────────────────────────────


class CarreraCreate(BaseModel):
    """Create a new academic program."""

    model_config = ConfigDict(extra="forbid")

    codigo: str = Field(..., min_length=1, max_length=20)
    nombre: str = Field(..., min_length=1, max_length=255)

    @model_validator(mode="before")
    @classmethod
    def _uppercase_codigo(cls, data: dict) -> dict:
        """Uppercase codigo before validation."""
        if isinstance(data, dict) and "codigo" in data:
            data["codigo"] = _validate_codigo(data["codigo"])
        return data


class CarreraUpdate(BaseModel):
    """Update an existing academic program."""

    model_config = ConfigDict(extra="forbid")

    codigo: Optional[str] = Field(None, min_length=1, max_length=20)
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    estado: Optional[str] = Field(None, pattern=r"^(Activa|Inactiva)$")

    @model_validator(mode="before")
    @classmethod
    def _uppercase_codigo(cls, data: dict) -> dict:
        """Uppercase codigo if provided."""
        if isinstance(data, dict) and "codigo" in data and data["codigo"] is not None:
            data["codigo"] = _validate_codigo(data["codigo"])
        return data


class CarreraResponse(BaseModel):
    """Carrera read response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    codigo: str
    nombre: str
    estado: str
    created_at: datetime
    updated_at: datetime


# ── Cohorte schemas ──────────────────────────────────────────────────────────


class CohorteCreate(BaseModel):
    """Create a new cohort."""

    model_config = ConfigDict(extra="forbid")

    carrera_id: str
    nombre: str = Field(..., min_length=1, max_length=100)
    anio: int = Field(..., ge=1900, le=2200)
    vig_desde: date
    vig_hasta: Optional[date] = None
    estado: Optional[str] = Field(None, pattern=r"^(Activa|Inactiva)$")

    @model_validator(mode="after")
    def _validate_date_range(self) -> "CohorteCreate":
        """Validate vig_desde <= vig_hasta if vig_hasta provided."""
        if self.vig_hasta is not None and self.vig_desde > self.vig_hasta:
            raise ValueError("vig_desde must be on or before vig_hasta")
        return self


class CohorteUpdate(BaseModel):
    """Update an existing cohort."""

    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    anio: Optional[int] = Field(None, ge=1900, le=2200)
    vig_desde: Optional[date] = None
    vig_hasta: Optional[date] = None
    estado: Optional[str] = Field(None, pattern=r"^(Activa|Inactiva)$")

    @model_validator(mode="after")
    def _validate_date_range(self) -> "CohorteUpdate":
        """Validate vig_desde <= vig_hasta if both are provided."""
        if self.vig_desde is not None and self.vig_hasta is not None:
            if self.vig_desde > self.vig_hasta:
                raise ValueError("vig_desde must be on or before vig_hasta")
        return self


class CohorteResponse(BaseModel):
    """Cohorte read response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    carrera_id: str
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: Optional[date] = None
    estado: str
    created_at: datetime
    updated_at: datetime


# ── Materia schemas ──────────────────────────────────────────────────────────


class MateriaCreate(BaseModel):
    """Create a new subject in the catalog."""

    model_config = ConfigDict(extra="forbid")

    codigo: str = Field(..., min_length=1, max_length=20)
    nombre: str = Field(..., min_length=1, max_length=255)

    @model_validator(mode="before")
    @classmethod
    def _uppercase_codigo(cls, data: dict) -> dict:
        """Uppercase codigo before validation."""
        if isinstance(data, dict) and "codigo" in data:
            data["codigo"] = _validate_codigo(data["codigo"])
        return data


class MateriaUpdate(BaseModel):
    """Update an existing subject."""

    model_config = ConfigDict(extra="forbid")

    codigo: Optional[str] = Field(None, min_length=1, max_length=20)
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    estado: Optional[str] = Field(None, pattern=r"^(Activa|Inactiva)$")

    @model_validator(mode="before")
    @classmethod
    def _uppercase_codigo(cls, data: dict) -> dict:
        """Uppercase codigo if provided."""
        if isinstance(data, dict) and "codigo" in data and data["codigo"] is not None:
            data["codigo"] = _validate_codigo(data["codigo"])
        return data


class MateriaResponse(BaseModel):
    """Materia read response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    codigo: str
    nombre: str
    estado: str
    created_at: datetime
    updated_at: datetime


# ── ProgramaMateria schemas ──────────────────────────────────────────────────


class ProgramaMateriaResponse(BaseModel):
    """ProgramaMateria read response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    materia_id: str
    carrera_id: str
    cohorte_id: str
    titulo: str
    referencia_archivo: str
    cargado_at: datetime


class ProgramaMateriaUploadResponse(BaseModel):
    """ProgramaMateria response after successful upload."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    titulo: str
    materia_id: str
    carrera_id: str
    cohorte_id: str
    cargado_at: datetime
