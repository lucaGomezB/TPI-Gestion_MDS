"""Pydantic schemas for user-facing materia endpoints.

Provides:
- ``MateriaResponse`` — lightweight materia view for the current user
  (derived from their asignaciones), matching the frontend ``Materia`` type.
"""

from pydantic import BaseModel, ConfigDict


class MateriaResponse(BaseModel):
    """User-facing materia summary derived from asignaciones.

    ``cohorte`` is the cohort display name (not the ID).
    ``comisiones`` comes from the asignacion's JSONB list.
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: str
    nombre: str
    cohorte: str
    comisiones: list[str] = []
    tenant_id: str
