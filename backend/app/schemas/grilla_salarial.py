"""Pydantic schemas for salary grid (C-18).

All schemas have ``extra='forbid'`` to reject undeclared fields.
Schema validators enforce:
- vig_desde <= vig_hasta (if vig_hasta provided)
- Rol must be one of COORDINADOR, NEXO, PROFESOR, TUTOR
- Monto must be positive (> 0)
"""

from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, model_validator
from pydantic import BaseModel as PydanticBaseModel

from app.models.grilla_salarial import RolSalarial


# ── Mixins ──────────────────────────────────────────────────────────────

class _ExtraForbid(PydanticBaseModel):
    """Base schema with from_attributes=True and extra='forbid'."""

    model_config: ConfigDict = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class _DateRangeValidator:
    """Mixin providing desde/hasta range validation."""

    @model_validator(mode="after")
    def _validate_date_range(self) -> "_DateRangeValidator":
        desde = getattr(self, "desde", None)
        hasta = getattr(self, "hasta", None)
        if desde is not None and hasta is not None and desde > hasta:
            raise ValueError("'desde' must be on or before 'hasta'")
        return self


# ── SalarioBase schemas ─────────────────────────────────────────────────

class SalarioBaseCreate(_ExtraForbid, _DateRangeValidator):
    """Schema for creating a new salary base entry."""

    rol: str = Field(
        ...,
        min_length=1,
        description="Role code: COORDINADOR, NEXO, PROFESOR, or TUTOR",
    )
    monto: float = Field(
        ...,
        gt=0,
        description="Base salary amount",
    )
    desde: date = Field(
        ...,
        description="Start date of validity",
    )
    hasta: Optional[date] = Field(
        default=None,
        description="End date of validity (null = open-ended)",
    )

    @model_validator(mode="after")
    def _validate_rol(self) -> "SalarioBaseCreate":
        valid_roles = {r.value for r in RolSalarial}
        if self.rol not in valid_roles:
            raise ValueError(
                f"Invalid rol '{self.rol}'. Must be one of: {', '.join(sorted(valid_roles))}"
            )
        return self


class SalarioBaseUpdate(_ExtraForbid, _DateRangeValidator):
    """Schema for updating a salary base entry (partial)."""

    rol: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Role code",
    )
    monto: Optional[float] = Field(
        default=None,
        gt=0,
        description="Base salary amount",
    )
    desde: Optional[date] = Field(
        default=None,
        description="Start date of validity",
    )
    hasta: Optional[date] = Field(
        default=None,
        description="End date of validity (null = open-ended)",
    )

    @model_validator(mode="after")
    def _validate_rol(self) -> "SalarioBaseUpdate":
        if self.rol is not None:
            valid_roles = {r.value for r in RolSalarial}
            if self.rol not in valid_roles:
                raise ValueError(
                    f"Invalid rol '{self.rol}'. Must be one of: "
                    f"{', '.join(sorted(valid_roles))}"
                )
        return self


class SalarioBaseResponse(_ExtraForbid):
    """Schema for salary base entry response."""

    id: str
    tenant_id: str
    rol: str
    monto: float
    desde: str
    hasta: Optional[str] = None
    created_at: str
    updated_at: str


# ── SalarioPlus schemas ─────────────────────────────────────────────────

class SalarioPlusCreate(_ExtraForbid, _DateRangeValidator):
    """Schema for creating a new salary plus entry."""

    grupo: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Subject group key",
    )
    rol: str = Field(
        ...,
        min_length=1,
        description="Role code: COORDINADOR, NEXO, PROFESOR, or TUTOR",
    )
    descripcion: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Description of the bonus",
    )
    monto: float = Field(
        ...,
        gt=0,
        description="Bonus amount",
    )
    desde: date = Field(
        ...,
        description="Start date of validity",
    )
    hasta: Optional[date] = Field(
        default=None,
        description="End date of validity (null = open-ended)",
    )

    @model_validator(mode="after")
    def _validate_rol(self) -> "SalarioPlusCreate":
        valid_roles = {r.value for r in RolSalarial}
        if self.rol not in valid_roles:
            raise ValueError(
                f"Invalid rol '{self.rol}'. Must be one of: {', '.join(sorted(valid_roles))}"
            )
        return self


class SalarioPlusUpdate(_ExtraForbid, _DateRangeValidator):
    """Schema for updating a salary plus entry (partial)."""

    grupo: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    rol: Optional[str] = Field(
        default=None,
        min_length=1,
    )
    descripcion: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    monto: Optional[float] = Field(
        default=None,
        gt=0,
    )
    desde: Optional[date] = Field(
        default=None,
    )
    hasta: Optional[date] = Field(
        default=None,
    )

    @model_validator(mode="after")
    def _validate_rol(self) -> "SalarioPlusUpdate":
        if self.rol is not None:
            valid_roles = {r.value for r in RolSalarial}
            if self.rol not in valid_roles:
                raise ValueError(
                    f"Invalid rol '{self.rol}'. Must be one of: "
                    f"{', '.join(sorted(valid_roles))}"
                )
        return self


class SalarioPlusResponse(_ExtraForbid):
    """Schema for salary plus entry response."""

    id: str
    tenant_id: str
    grupo: str
    rol: str
    descripcion: str
    monto: float
    desde: str
    hasta: Optional[str] = None
    created_at: str
    updated_at: str


# ── GrupoMateria schemas ───────────────────────────────────────────────

class GrupoMateriaCreate(_ExtraForbid):
    """Schema for creating a new subject group."""

    grupo: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Unique group key within tenant",
    )
    descripcion: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional description",
    )


class GrupoMateriaUpdate(_ExtraForbid):
    """Schema for updating a subject group (partial)."""

    grupo: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=20,
    )
    descripcion: Optional[str] = Field(
        default=None,
        max_length=255,
    )


class GrupoMateriaResponse(_ExtraForbid):
    """Schema for subject group response."""

    id: str
    tenant_id: str
    grupo: str
    descripcion: Optional[str] = None
    created_at: str
    updated_at: str


# ── Materia assignment schemas ──────────────────────────────────────────

class MateriasAsignarRequest(_ExtraForbid):
    """Schema for assigning subjects to a group."""

    materia_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of materia UUIDs to assign",
    )


class MateriaGrupoResponse(_ExtraForbid):
    """Schema for materia-group association response."""

    id: str
    materia_id: str
    grupo_id: str
    tenant_id: str
    created_at: str
