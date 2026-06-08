"""Salary grid models — SalarioBase, SalarioPlus, GrupoMateria, and MateriaGrupo.

Implements E17 (SalarioBase), E18 (SalarioPlus), and supporting entities for
configurable subject groups and their N:N relationship with Materia.

Design decisions (per C-18 design.md):
- D-02: RolSalarial enum with 4 fixed roles (COORDINADOR, NEXO, PROFESOR, TUTOR)
- D-04: GrupoMateria with tenant-scoped textual key (1-20 chars)
- D-05: No AuditMixin — temporal versioning via desde/hasta replaces soft-delete
"""

import enum

from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin


class RolSalarial(str, enum.Enum):
    """Fixed roles eligible for base salary (RN-32)."""

    COORDINADOR = "COORDINADOR"
    NEXO = "NEXO"
    PROFESOR = "PROFESOR"
    TUTOR = "TUTOR"


class SalarioBase(AppModel, TimestampMixin, TenantMixin):
    """Base salary amount for a specific role with temporal validity (E17)."""

    __tablename__ = "salarios_base"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "rol", "desde",
            name="uq_salario_base_tenant_rol_desde",
        ),
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    rol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    monto: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    desde: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    hasta: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )


class SalarioPlus(AppModel, TimestampMixin, TenantMixin):
    """Bonus pay for a combination of subject group and role (E18)."""

    __tablename__ = "salarios_plus"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "grupo", "rol", "desde",
            name="uq_salario_plus_tenant_grupo_rol_desde",
        ),
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    grupo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    rol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    descripcion: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    monto: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    desde: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    hasta: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )


class GrupoMateria(AppModel, TimestampMixin, TenantMixin):
    """A group key that categorizes subjects (e.g., 'PROG', 'BD', 'MAT').

    Groups are tenant-scoped and configurable. A subject can belong to
    multiple groups via the MateriaGrupo join table.
    """

    __tablename__ = "grupos_materia"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "grupo",
            name="uq_grupo_materia_tenant_grupo",
        ),
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    grupo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    descripcion: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    materias: Mapped[list["MateriaGrupo"]] = relationship(
        "MateriaGrupo",
        back_populates="grupo",
        cascade="all, delete-orphan",
    )


class MateriaGrupo(AppModel, TenantMixin):
    """N:N relationship between subjects (Materia) and subject groups."""

    __tablename__ = "materias_grupo"

    __table_args__ = (
        UniqueConstraint(
            "materia_id", "grupo_id",
            name="uq_materia_grupo_materia_grupo",
        ),
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    materia_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materias.id", ondelete="CASCADE"),
        nullable=False,
    )
    grupo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("grupos_materia.id", ondelete="CASCADE"),
        nullable=False,
    )

    grupo: Mapped["GrupoMateria"] = relationship(
        "GrupoMateria",
        back_populates="materias",
    )
