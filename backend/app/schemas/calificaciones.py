"""Pydantic schemas for calificaciones (grades) endpoints.

All schemas use ``extra='forbid'`` per project convention.

Schemas:
- CalificacionResponse: single grade record response
- CalificacionListResponse: paginated list of grades
- PreviewActividadOut: detected activity metadata in preview mode
- PreviewResultOut: preview response for import
- ImportConfirmIn: request body for import confirmation
- ImportResultOut: result of confirm import
- UmbralMateriaUpdateIn: create/update threshold
- UmbralMateriaOut: threshold response
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CalificacionResponse(BaseModel):
    """A grade record for a student on an activity."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    entrada_padron_id: str
    materia_id: str
    actividad: str
    nota_numerica: float | None = None
    nota_textual: str | None = None
    aprobado: bool
    origen: str
    importado_at: datetime


class CalificacionListResponse(BaseModel):
    """Paginated list of grade records."""

    model_config = ConfigDict(extra="forbid")

    items: list[CalificacionResponse]
    total: int


class PreviewActividadOut(BaseModel):
    """Metadata about a detected activity in the uploaded file."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    tipo: str  # "numerica" | "textual"
    columna: str
    total_alumnos: int


class PreviewResultOut(BaseModel):
    """Response for preview mode — no data persisted."""

    model_config = ConfigDict(extra="forbid")

    actividades: list[PreviewActividadOut]
    total_alumnos: int
    archivo: str


class ImportConfirmIn(BaseModel):
    """Request body to confirm an import with selected activities."""

    model_config = ConfigDict(extra="forbid")

    actividades_seleccionadas: list[str] = Field(
        ..., min_length=1, description="Activity names to include in the import"
    )


class ImportResultOut(BaseModel):
    """Result of a confirmed grade import."""

    model_config = ConfigDict(extra="forbid")

    total_importados: int
    actividades: list[str]
    mensaje: str = "Calificaciones importadas exitosamente"


class UmbralMateriaUpdateIn(BaseModel):
    """Create or update an approval threshold."""

    model_config = ConfigDict(extra="forbid")

    umbral_pct: int | None = Field(
        default=None, ge=0, le=100, description="Percentage threshold (0-100)"
    )
    valores_aprobatorios: list[str] | None = Field(
        default=None,
        min_length=1,
        description="Approved textual grade values",
    )


class UmbralMateriaOut(BaseModel):
    """Approval threshold configuration response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str | None = None
    asignacion_id: str
    materia_id: str
    umbral_pct: int
    valores_aprobatorios: list[str]
