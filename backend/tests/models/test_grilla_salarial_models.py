"""Tests for salary grid models — SalarioBase, SalarioPlus, GrupoMateria, MateriaGrupo."""

import pytest
from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin


class TestSalarioBaseModel:
    """SalarioBase model — per-role base salary (E17)."""

    def test_extends_app_model(self):
        from app.models.grilla_salarial import SalarioBase

        assert issubclass(SalarioBase, AppModel)

    def test_has_timestamp_mixin(self):
        from app.models.grilla_salarial import SalarioBase

        assert issubclass(SalarioBase, TimestampMixin)

    def test_has_tenant_mixin(self):
        from app.models.grilla_salarial import SalarioBase

        assert issubclass(SalarioBase, TenantMixin)

    def test_tablename_is_salarios_base(self):
        from app.models.grilla_salarial import SalarioBase

        assert SalarioBase.__tablename__ == "salarios_base"

    def test_has_rol_field(self):
        from app.models.grilla_salarial import SalarioBase

        assert hasattr(SalarioBase, "rol")

    def test_rol_is_string_20(self):
        from app.models.grilla_salarial import SalarioBase

        col = SalarioBase.__table__.c["rol"]
        assert isinstance(col.type, String)
        assert col.type.length == 20

    def test_has_monto_field(self):
        from app.models.grilla_salarial import SalarioBase

        assert hasattr(SalarioBase, "monto")

    def test_monto_is_numeric_12_2(self):
        from app.models.grilla_salarial import SalarioBase

        col = SalarioBase.__table__.c["monto"]
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 12
        assert col.type.scale == 2

    def test_has_desde_field(self):
        from app.models.grilla_salarial import SalarioBase

        assert hasattr(SalarioBase, "desde")

    def test_desde_is_date_not_nullable(self):
        from app.models.grilla_salarial import SalarioBase

        col = SalarioBase.__table__.c["desde"]
        assert isinstance(col.type, Date)
        assert not col.nullable

    def test_hasta_is_date_nullable(self):
        from app.models.grilla_salarial import SalarioBase

        col = SalarioBase.__table__.c["hasta"]
        assert isinstance(col.type, Date)
        assert col.nullable

    def test_tenant_id_not_nullable(self):
        from app.models.grilla_salarial import SalarioBase

        col = SalarioBase.__table__.c["tenant_id"]
        assert not col.nullable

    def test_unique_constraint_tenant_rol_desde(self):
        from app.models.grilla_salarial import SalarioBase

        uq = SalarioBase.__table_args__
        found = False
        for arg in uq:
            if hasattr(arg, "columns"):
                cols = [c.name for c in arg.columns]
                if "tenant_id" in cols and "rol" in cols and "desde" in cols:
                    found = True
        assert found, "Expected UniqueConstraint on (tenant_id, rol, desde)"


class TestSalarioPlusModel:
    """SalarioPlus model — bonus pay per group x role (E18)."""

    def test_extends_app_model(self):
        from app.models.grilla_salarial import SalarioPlus

        assert issubclass(SalarioPlus, AppModel)

    def test_has_timestamp_mixin(self):
        from app.models.grilla_salarial import SalarioPlus

        assert issubclass(SalarioPlus, TimestampMixin)

    def test_has_tenant_mixin(self):
        from app.models.grilla_salarial import SalarioPlus

        assert issubclass(SalarioPlus, TenantMixin)

    def test_tablename_is_salarios_plus(self):
        from app.models.grilla_salarial import SalarioPlus

        assert SalarioPlus.__tablename__ == "salarios_plus"

    def test_has_grupo_field(self):
        from app.models.grilla_salarial import SalarioPlus

        assert hasattr(SalarioPlus, "grupo")

    def test_has_rol_field(self):
        from app.models.grilla_salarial import SalarioPlus

        assert hasattr(SalarioPlus, "rol")

    def test_has_descripcion_field(self):
        from app.models.grilla_salarial import SalarioPlus

        assert hasattr(SalarioPlus, "descripcion")

    def test_has_monto_field(self):
        from app.models.grilla_salarial import SalarioPlus

        assert hasattr(SalarioPlus, "monto")

    def test_monto_is_numeric_12_2(self):
        from app.models.grilla_salarial import SalarioPlus

        col = SalarioPlus.__table__.c["monto"]
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 12
        assert col.type.scale == 2

    def test_hasta_is_date_nullable(self):
        from app.models.grilla_salarial import SalarioPlus

        col = SalarioPlus.__table__.c["hasta"]
        assert isinstance(col.type, Date)
        assert col.nullable

    def test_unique_constraint_tenant_grupo_rol_desde(self):
        from app.models.grilla_salarial import SalarioPlus

        uq = SalarioPlus.__table_args__
        found = False
        for arg in uq:
            if hasattr(arg, "columns"):
                cols = [c.name for c in arg.columns]
                if "tenant_id" in cols and "grupo" in cols and "rol" in cols and "desde" in cols:
                    found = True
        assert found, "Expected UniqueConstraint on (tenant_id, grupo, rol, desde)"


class TestGrupoMateriaModel:
    """GrupoMateria model — configurable subject groups."""

    def test_extends_app_model(self):
        from app.models.grilla_salarial import GrupoMateria

        assert issubclass(GrupoMateria, AppModel)

    def test_has_timestamp_mixin(self):
        from app.models.grilla_salarial import GrupoMateria

        assert issubclass(GrupoMateria, TimestampMixin)

    def test_has_tenant_mixin(self):
        from app.models.grilla_salarial import GrupoMateria

        assert issubclass(GrupoMateria, TenantMixin)

    def test_tablename_is_grupos_materia(self):
        from app.models.grilla_salarial import GrupoMateria

        assert GrupoMateria.__tablename__ == "grupos_materia"

    def test_has_grupo_field(self):
        from app.models.grilla_salarial import GrupoMateria

        assert hasattr(GrupoMateria, "grupo")

    def test_grupo_is_string_20(self):
        from app.models.grilla_salarial import GrupoMateria

        col = GrupoMateria.__table__.c["grupo"]
        assert isinstance(col.type, String)
        assert col.type.length == 20

    def test_descripcion_is_nullable(self):
        from app.models.grilla_salarial import GrupoMateria

        col = GrupoMateria.__table__.c["descripcion"]
        assert col.nullable

    def test_unique_constraint_tenant_grupo(self):
        from app.models.grilla_salarial import GrupoMateria

        uq = GrupoMateria.__table_args__
        found = False
        for arg in uq:
            if hasattr(arg, "columns"):
                cols = [c.name for c in arg.columns]
                if "tenant_id" in cols and "grupo" in cols:
                    found = True
        assert found, "Expected UniqueConstraint on (tenant_id, grupo)"


class TestMateriaGrupoModel:
    """MateriaGrupo model — N:N relationship between subjects and groups."""

    def test_extends_app_model(self):
        from app.models.grilla_salarial import MateriaGrupo

        assert issubclass(MateriaGrupo, AppModel)

    def test_has_tenant_mixin(self):
        from app.models.grilla_salarial import MateriaGrupo

        assert issubclass(MateriaGrupo, TenantMixin)

    def test_tablename_is_materias_grupo(self):
        from app.models.grilla_salarial import MateriaGrupo

        assert MateriaGrupo.__tablename__ == "materias_grupo"

    def test_has_materia_id_field(self):
        from app.models.grilla_salarial import MateriaGrupo

        assert hasattr(MateriaGrupo, "materia_id")

    def test_has_grupo_id_field(self):
        from app.models.grilla_salarial import MateriaGrupo

        assert hasattr(MateriaGrupo, "grupo_id")

    def test_materia_id_not_nullable(self):
        from app.models.grilla_salarial import MateriaGrupo

        col = MateriaGrupo.__table__.c["materia_id"]
        assert not col.nullable

    def test_grupo_id_not_nullable(self):
        from app.models.grilla_salarial import MateriaGrupo

        col = MateriaGrupo.__table__.c["grupo_id"]
        assert not col.nullable

    def test_unique_constraint_materia_grupo(self):
        from app.models.grilla_salarial import MateriaGrupo

        uq = MateriaGrupo.__table_args__
        found = False
        for arg in uq:
            if hasattr(arg, "columns"):
                cols = [c.name for c in arg.columns]
                if "materia_id" in cols and "grupo_id" in cols:
                    found = True
        assert found, "Expected UniqueConstraint on (materia_id, grupo_id)"
