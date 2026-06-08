"""Pydantic schemas for Coloquio management.

All schemas use ``extra='forbid'`` per project convention.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Day schema ────────────────────────────────────────────────────────────────


class DiaColoquioSchema(BaseModel):
    """A single day configuration within a coloquio convocatoria."""

    model_config = ConfigDict(extra="forbid")

    fecha: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    cupos: int = Field(..., ge=1, le=999)
    reservados: int = Field(default=0, ge=0)


class DiaColoquioResponse(BaseModel):
    """Day configuration in responses."""

    model_config = ConfigDict(extra="forbid")

    fecha: str
    cupos: int
    reservados: int


# ── EvaluacionColoquio ────────────────────────────────────────────────────────


class EvaluacionColoquioCreate(BaseModel):
    """Create a new coloquio convocatoria."""

    model_config = ConfigDict(extra="forbid")

    titulo: str = Field(..., min_length=1, max_length=200)
    dias: list[DiaColoquioSchema] = Field(default=[], min_length=1)
    activa: bool = True


class EvaluacionColoquioResponse(BaseModel):
    """Coloquio convocatoria read response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    materia_id: str
    titulo: str
    dias: list[DiaColoquioResponse]
    creado_por: str | None = None
    activa: bool
    cohorte_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ColoquioListResponse(BaseModel):
    """Paginated wrapper for coloquio list responses."""

    model_config = ConfigDict(extra="forbid")

    items: list[EvaluacionColoquioResponse]
    total: int


# ── ReservaColoquio ───────────────────────────────────────────────────────────


class ReservaColoquioCreate(BaseModel):
    """Create a student reservation for a coloquio turn."""

    model_config = ConfigDict(extra="forbid")

    dia: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")


class ReservaColoquioResponse(BaseModel):
    """Reservation read response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    evaluacion_id: str
    alumno_id: str
    dia: date
    confirmada: bool
    created_at: datetime
    updated_at: datetime


# ── ResultadoColoquio ─────────────────────────────────────────────────────────


class ResultadoColoquioCreate(BaseModel):
    """Register a student's coloquio result."""

    model_config = ConfigDict(extra="forbid")

    alumno_id: str
    nota: float | None = Field(None, ge=0, le=10)
    aprobado: bool


class ResultadoColoquioResponse(BaseModel):
    """Result read response."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    evaluacion_id: str
    alumno_id: str
    nota: float | None = None
    aprobado: bool
    registrado_por: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Agenda ────────────────────────────────────────────────────────────────────


class ReservaEnAgenda(BaseModel):
    """A reservation entry within an agenda day view."""

    model_config = ConfigDict(extra="forbid")

    alumno_id: str
    alumno_nombre: str | None = None
    alumno_apellidos: str | None = None
    confirmada: bool


class DiaAgenda(BaseModel):
    """A day entry within the consolidated agenda."""

    model_config = ConfigDict(extra="forbid")

    fecha: str
    cupos: int
    reservados: int
    reservas: list[ReservaEnAgenda]


class AgendaColoquioResponse(BaseModel):
    """Consolidated agenda for a coloquio convocatoria."""

    model_config = ConfigDict(extra="forbid")

    evaluacion_id: str
    titulo: str
    dias: list[DiaAgenda]


# ── Importar alumnos ──────────────────────────────────────────────────────────


class ImportarAlumnosRequest(BaseModel):
    """Request to import students into a coloquio from materia padron."""

    model_config = ConfigDict(extra="forbid")

    evaluacion_id: str


class AlumnoImportado(BaseModel):
    """An imported student entry in the import response."""

    model_config = ConfigDict(extra="forbid")

    usuario_id: str | None = None
    nombre: str
    apellidos: str
    email: str


class ImportarAlumnosResponse(BaseModel):
    """Response after importing students to a coloquio."""

    model_config = ConfigDict(extra="forbid")

    evaluacion_id: str
    alumnos_importados: list[AlumnoImportado]
    total_importados: int


# ── Metricas admin ────────────────────────────────────────────────────────────


class MetricasColoquioResponse(BaseModel):
    """Admin metrics for coloquio overview."""

    model_config = ConfigDict(extra="forbid")

    total_convocatorias: int
    total_alumnos_importados: int
    total_reservas_activas: int
    total_resultados_registrados: int
