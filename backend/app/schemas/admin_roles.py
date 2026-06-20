"""Pydantic schemas for admin role management.

All schemas use ``extra='forbid'`` to reject undeclared fields (hard rule).

Schemas:
- ``RolCreate``: nombre, descripcion, permisos
- ``RolUpdate``: all optional, partial update (incl. activo for soft-delete)
- ``RolResponse``: all safe fields
- ``PermissionsResponse``: grouped permissions for UI rendering
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RolCreate(BaseModel):
    """Schema for creating a new role via admin panel."""

    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Role name (unique within tenant, e.g. 'EDITOR')",
    )
    descripcion: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Human-readable description of the role",
    )
    permisos: list[str] = Field(
        default_factory=list,
        description="List of permission strings (e.g. ['avisos:ver', 'calificaciones:importar'])",
    )


class RolUpdate(BaseModel):
    """Schema for partially updating a role via admin panel.

    All fields are optional — only the provided fields are updated.
    """

    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="New role name (must be unique within tenant)",
    )
    descripcion: Optional[str] = Field(
        default=None,
        max_length=255,
        description="New role description",
    )
    permisos: Optional[list[str]] = Field(
        default=None,
        description="Replacement list of permission strings (replaces all if provided)",
    )
    activo: Optional[bool] = Field(
        default=None,
        description="Set false to soft-delete, true to reactivate",
    )


class RolResponse(BaseModel):
    """Safe role representation for admin API responses."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    nombre: str
    descripcion: Optional[str] = None
    permisos: list[str] = Field(default_factory=list, description="List of permission strings")
    activo: bool = Field(description="True if estado == 'Activo'")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ModuloPermisos(BaseModel):
    """Group of permissions for a single module."""

    model_config = ConfigDict(extra="forbid")

    modulo: str = Field(description="Module name (e.g. 'avisos', 'calificaciones')")
    permisos: list[str] = Field(description="Permission strings for this module")


class PermissionsResponse(BaseModel):
    """All available permissions, grouped by module for UI rendering."""

    model_config = ConfigDict(extra="forbid")

    modulos: list[ModuloPermisos] = Field(description="Permissions grouped by module")
    todos: list[str] = Field(description="Flat list of all permission strings")
