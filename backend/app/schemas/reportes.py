"""Pydantic schemas for reportes endpoints.

All schemas use ``extra='forbid'`` per project convention.

Schemas (F2.5-F2.9):
- NotaFinalEntryOut: single student final grade record
- NotasFinalesResponse: list of final grades with aggregate metrics
- ExportAtrasadoEntryOut: single uncorrected TP record
- ExportAtrasadosResponse: list of uncorrected TPs
- MonitorEntryOut: single monitor entry with activity status
- MonitorGeneralResponse: monitor list with aggregate metrics
- SeguimientoActividadOut: single activity status in seguimiento
- SeguimientoEntryOut: single student seguimiento record
- SeguimientoResponse: list of seguimiento entries
"""

from pydantic import BaseModel, ConfigDict


# ── Notas Finales (F2.5) ─────────────────────────────────────────────────────


class NotaFinalEntryOut(BaseModel):
    """A single student's final grade record."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: str
    nombre: str
    apellidos: str
    comision: str | None = None
    total_actividades: int
    nota_final: float
    estado: str  # "aprobado" | "reprobado"


class NotasFinalesResponse(BaseModel):
    """Response for notas-finales endpoint."""

    model_config = ConfigDict(extra="forbid")

    items: list[NotaFinalEntryOut]
    total: int
    total_alumnos: int
    promedio_general: float


# ── Export Atrasados (F2.6) ──────────────────────────────────────────────────


class ExportAtrasadoEntryOut(BaseModel):
    """A single uncorrected TP record."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    apellidos: str
    comision: str | None = None
    actividad: str
    estado: str = "sin_corregir"


class ExportAtrasadosResponse(BaseModel):
    """Response for export-atrasados endpoint."""

    model_config = ConfigDict(extra="forbid")

    items: list[ExportAtrasadoEntryOut]
    total: int


# ── Monitor General (F2.7) ───────────────────────────────────────────────────


class MonitorEntryOut(BaseModel):
    """A single monitor entry with activity status."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: str
    nombre: str
    apellidos: str
    comision: str | None = None
    regional: str | None = None
    materia_nombre: str
    materia_id: str
    total_actividades: int
    total_aprobadas: int
    total_pendientes: int
    ultima_actividad: str | None = None


class MonitorGeneralResponse(BaseModel):
    """Response for monitor general endpoint."""

    model_config = ConfigDict(extra="forbid")

    items: list[MonitorEntryOut]
    total: int
    total_alumnos: int
    total_materias: int
    total_actividades: int
    total_aprobadas: int


# ── Seguimiento (F2.8, F2.9) ─────────────────────────────────────────────────


class SeguimientoActividadOut(BaseModel):
    """A single activity status within seguimiento."""

    model_config = ConfigDict(extra="forbid")

    actividad_nombre: str
    nota_numerica: float | None = None
    nota_textual: str | None = None
    aprobado: bool


class SeguimientoEntryOut(BaseModel):
    """A single student's seguimiento record."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: str
    nombre: str
    apellidos: str
    comision: str | None = None
    actividades: list[SeguimientoActividadOut]
    total_actividades: int
    total_aprobadas: int
    porcentaje_cumplimiento: float


class SeguimientoResponse(BaseModel):
    """Response for seguimiento endpoint."""

    model_config = ConfigDict(extra="forbid")

    items: list[SeguimientoEntryOut]
    total: int
    total_alumnos: int
    promedio_cumplimiento: float
