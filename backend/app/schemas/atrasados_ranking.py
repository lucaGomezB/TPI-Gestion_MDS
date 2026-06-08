"""Pydantic schemas for atrasados-ranking endpoints.

All schemas use ``extra='forbid'`` per project convention.

Schemas:
- AlumnoAtrasadoOut: single at-risk student record
- AtrasadosListResponse: paginated list of at-risk students
- RankingEntryOut: single ranking entry
- RankingListResponse: list of ranking entries
- ActividadMetricaOut: activity metric with counts
- ReportesOut: consolidated subject metrics
"""

from pydantic import BaseModel, ConfigDict


class AlumnoAtrasadoOut(BaseModel):
    """An at-risk student record."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    razon: str  # "faltante" | "nota_baja"
    nota_minima: float | None = None
    umbral: int | None = None
    total_actividades: int


class MetricsOut(BaseModel):
    """Metrics summary for atrasados list."""

    model_config = ConfigDict(extra="forbid")

    total_alumnos: int
    total_atrasados: int


class AtrasadosListResponse(BaseModel):
    """Response for atrasados list endpoint."""

    model_config = ConfigDict(extra="forbid")

    items: list[AlumnoAtrasadoOut]
    total: int
    metrics: MetricsOut


class RankingEntryOut(BaseModel):
    """A single student ranking entry."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    apellidos: str
    comision: str | None = None
    total_aprobadas: int
    total_actividades: int
    porcentaje_aprobacion: float


class RankingListResponse(BaseModel):
    """Response for ranking endpoint."""

    model_config = ConfigDict(extra="forbid")

    items: list[RankingEntryOut]
    total: int


class ActividadMetricaOut(BaseModel):
    """Activity metric with student count."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    total_alumnos: int
    total_aprobados: int


class ReportesOut(BaseModel):
    """Consolidated subject metrics."""

    model_config = ConfigDict(extra="forbid")

    total_alumnos: int
    alumnos_con_calificaciones: int
    total_atrasados: int
    total_aprobadas: int
    total_calificaciones: int
    actividades: list[ActividadMetricaOut]
    porcentaje_atrasados: float
