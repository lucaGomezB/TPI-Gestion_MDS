"""Pydantic schemas for padron de alumnos (roster) endpoints.

All schemas use ``extra='forbid'`` per project convention.

Schemas:
- VersionPadronOut, EntradaPadronOut: read responses
- VersionHistoryOut: version list with total_entradas
- ImportResultOut: result of an import operation
- PadronListOut: list of active entries
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EntradaPadronOut(BaseModel):
    """Student entry within a padron version."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    version_id: str
    tenant_id: str
    usuario_id: str | None = None
    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    regional: str | None = None
    created_at: datetime
    updated_at: datetime


class VersionPadronOut(BaseModel):
    """Padron import version."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    materia_id: str
    cohorte_id: str
    cargado_por: str | None = None
    cargado_at: datetime
    activa: bool
    total_entradas: int
    created_at: datetime
    updated_at: datetime


class VersionHistoryOut(BaseModel):
    """Version history item with entry count."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    materia_id: str
    cohorte_id: str
    cargado_por: str | None = None
    cargado_at: datetime
    activa: bool
    total_entradas: int
    created_at: datetime


class ImportResultOut(BaseModel):
    """Result of a roster import operation."""

    model_config = ConfigDict(extra="forbid")

    version_id: str
    total_imported: int
    mensaje: str = "Padron importado exitosamente"


class PadronListOut(BaseModel):
    """Active padron entries list."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    version_id: str
    usuario_id: str | None = None
    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    regional: str | None = None
