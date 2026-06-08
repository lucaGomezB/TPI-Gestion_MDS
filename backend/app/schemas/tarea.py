"""Pydantic schemas for Tarea (E12) and ComentarioTarea.

All schemas use ``extra='forbid'`` to reject undeclared fields,
inheriting from ``BaseSchema``.
"""

from datetime import datetime

from pydantic import Field, field_validator

from app.models.tarea import EstadoTarea
from app.schemas.base import BaseSchema


# ── Tarea schemas ────────────────────────────────────────────────────────


class TareaCreate(BaseSchema):
    """Request schema for creating a new Tarea (POST /api/tareas)."""

    materia_id: str | None = Field(default=None, description="Materia UUID (nullable for institutional tasks)")
    asignado_a: str = Field(..., description="Usuario UUID assigned to the task")
    descripcion: str = Field(..., min_length=1, description="Task description")
    contexto_id: str | None = Field(default=None, description="Optional UUID reference to any domain entity")


class TareaRead(BaseSchema):
    """Response schema for a Tarea (personal task list view)."""

    id: str
    tenant_id: str
    materia_id: str | None = None
    asignado_a: str
    asignado_por: str
    estado: str
    descripcion: str
    contexto_id: str | None = None
    created_at: datetime
    updated_at: datetime


class TareaReadAdmin(BaseSchema):
    """Response schema for a Tarea (admin global view)."""

    id: str
    tenant_id: str
    materia_id: str | None = None
    asignado_a: str
    asignado_por: str
    estado: str
    descripcion: str
    contexto_id: str | None = None
    created_at: datetime
    updated_at: datetime
    comentario_count: int = Field(default=0, description="Number of comments on this task")


class TareaEstadoUpdate(BaseSchema):
    """Request schema for updating a Tarea's estado (PUT /api/tareas/{id}/estado)."""

    estado: str = Field(..., description="New estado value")

    @field_validator("estado")
    @classmethod
    def validate_estado(cls, v: str) -> str:
        """Validate that the estado value is one of the allowed values."""
        valid_values = {e.value for e in EstadoTarea}
        if v not in valid_values:
            raise ValueError(
                f"Estado invalido: '{v}'. Debe ser uno de: {', '.join(sorted(valid_values))}"
            )
        return v


class TareaFilter(BaseSchema):
    """Query parameters for filtering tareas lists.

    Used by both ``GET /api/tareas`` and ``GET /api/admin/tareas``.
    Admin endpoints also support ``asignado_a``, ``asignado_por``, and ``q``.
    """

    estado: str | None = Field(default=None, description="Filter by estado")
    materia_id: str | None = Field(default=None, description="Filter by materia UUID")
    asignado_a: str | None = Field(default=None, description="Filter by assigned user UUID (admin only)")
    asignado_por: str | None = Field(default=None, description="Filter by assigner user UUID (admin only)")
    q: str | None = Field(default=None, description="Free-text search in descripcion (admin only)")


# ── ComentarioTarea schemas ──────────────────────────────────────────────


class ComentarioCreate(BaseSchema):
    """Request schema for creating a comment on a Tarea (POST /api/tareas/{id}/comentarios)."""

    texto: str = Field(..., min_length=1, description="Comment text")


class ComentarioRead(BaseSchema):
    """Response schema for a comment on a Tarea."""

    id: str
    tenant_id: str
    tarea_id: str
    autor_id: str
    texto: str
    created_at: datetime
