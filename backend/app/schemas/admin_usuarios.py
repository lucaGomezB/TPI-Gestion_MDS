"""Pydantic schemas for admin user management.

All schemas use ``extra='forbid'`` to reject undeclared fields (hard rule).

Schemas:
- ``UsuarioCreate``: email, nombre, apellidos, password, facturador, roles
- ``UsuarioUpdate``: all optional, partial update
- ``UsuarioResponse``: safe fields only (no password_hash, no PII beyond email)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UsuarioCreate(BaseModel):
    """Schema for creating a new user via admin panel."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., min_length=3, max_length=255, description="User email address")
    nombre: str = Field(..., min_length=1, max_length=100, description="First name")
    apellidos: str = Field(..., min_length=1, max_length=200, description="Last names")
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Plaintext password (auto-generated if omitted)",
    )
    roles: list[str] = Field(
        default_factory=list,
        min_length=1,
        description="List of role names to assign (e.g. ['PROFESOR', 'TUTOR'])",
    )
    facturador: bool = Field(default=False, description="Whether this user can issue invoices")
    regional: Optional[str] = Field(default=None, max_length=100, description="Regional office")
    legajo: Optional[str] = Field(default=None, max_length=50, description="Legacy file number")
    legajo_profesional: Optional[str] = Field(
        default=None, max_length=50, description="Professional file number"
    )
    banco: Optional[str] = Field(default=None, max_length=100, description="Bank name")
    dni: Optional[str] = Field(default=None, max_length=20, description="DNI (encrypted at rest)")
    cuil: Optional[str] = Field(default=None, max_length=20, description="CUIL (encrypted at rest)")
    cbu: Optional[str] = Field(default=None, max_length=22, description="CBU (encrypted at rest)")
    alias_cbu: Optional[str] = Field(default=None, max_length=50, description="CBU alias (encrypted at rest)")


class UsuarioUpdate(BaseModel):
    """Schema for partially updating a user via admin panel.

    All fields are optional — only the provided fields are updated.
    """

    model_config = ConfigDict(extra="forbid")

    email: Optional[str] = Field(default=None, min_length=3, max_length=255, description="User email address")
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100, description="First name")
    apellidos: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Last names")
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="New plaintext password (only set if provided)",
    )
    roles: Optional[list[str]] = Field(
        default=None,
        description="List of role names to assign (replaces all existing roles if provided)",
    )
    facturador: Optional[bool] = Field(default=None, description="Whether this user can issue invoices")
    regional: Optional[str] = Field(default=None, max_length=100, description="Regional office")
    legajo: Optional[str] = Field(default=None, max_length=50, description="Legacy file number")
    legajo_profesional: Optional[str] = Field(
        default=None, max_length=50, description="Professional file number"
    )
    banco: Optional[str] = Field(default=None, max_length=100, description="Bank name")
    activo: Optional[bool] = Field(
        default=None,
        description="Set false to soft-delete the user (estado = 'Inactivo')",
    )
    dni: Optional[str] = Field(default=None, max_length=20, description="DNI (encrypted at rest)")
    cuil: Optional[str] = Field(default=None, max_length=20, description="CUIL (encrypted at rest)")
    cbu: Optional[str] = Field(default=None, max_length=22, description="CBU (encrypted at rest)")
    alias_cbu: Optional[str] = Field(default=None, max_length=50, description="CBU alias (encrypted at rest)")


class UsuarioResponse(BaseModel):
    """Safe user representation for admin API responses.

    Excludes password_hash, totp_secret, and encrypted PII fields
    beyond email (which is needed for display).
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    nombre: str
    apellidos: str
    email: str
    roles: list[str] = Field(default_factory=list, description="Assigned role names")
    facturador: bool = False
    regional: Optional[str] = None
    legajo: Optional[str] = None
    legajo_profesional: Optional[str] = None
    banco: Optional[str] = None
    activo: bool = Field(description="True if estado == 'Activo'")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
