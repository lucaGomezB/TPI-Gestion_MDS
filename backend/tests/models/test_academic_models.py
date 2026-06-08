"""Tests for academic structure models — Carrera, Cohorte, Materia, ProgramaMateria."""

import pytest
from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped

from app.models.base import AppModel
from app.models.mixins import AuditMixin, EstadoAcademico, TenantMixin, TimestampMixin


class TestCarreraModel:
    """Carrera model — academic program."""

    def test_extends_app_model(self):
        from app.models.carrera import Carrera

        assert issubclass(Carrera, AppModel)

    def test_has_timestamp_mixin(self):
        from app.models.carrera import Carrera

        assert issubclass(Carrera, TimestampMixin)

    def test_has_tenant_mixin(self):
        from app.models.carrera import Carrera

        assert issubclass(Carrera, TenantMixin)

    def test_tablename_is_carreras(self):
        from app.models.carrera import Carrera

        assert Carrera.__tablename__ == "carreras"

    def test_has_codigo(self):
        from app.models.carrera import Carrera

        assert hasattr(Carrera, "codigo")

    def test_codigo_is_string(self):
        from app.models.carrera import Carrera

        ann = Carrera.__annotations__["codigo"]
        assert "str" in str(ann)

    def test_has_nombre(self):
        from app.models.carrera import Carrera

        assert hasattr(Carrera, "nombre")

    def test_estado_uses_estado_academico(self):
        from app.models.carrera import Carrera

        ann = Carrera.__annotations__["estado"]
        assert "EstadoAcademico" in str(ann)

    def test_tenant_id_not_nullable(self):
        from app.models.carrera import Carrera

        col = getattr(Carrera, "tenant_id")
        assert hasattr(col, "expression")

    def test_unique_constraint_on_tenant_codigo(self):
        from app.models.carrera import Carrera

        uq = Carrera.__table_args__
        has_uq = False
        for arg in uq:
            if hasattr(arg, "columns"):
                cols = [str(c) for c in arg.columns] if hasattr(arg, "columns") else []
                if "tenant_id" in str(arg) and "codigo" in str(arg):
                    has_uq = True
        assert has_uq, "Expected UniqueConstraint on (tenant_id, codigo)"


class TestCohorteModel:
    """Cohorte model — cohort within a carrera."""

    def test_extends_app_model(self):
        from app.models.cohorte import Cohorte

        assert issubclass(Cohorte, AppModel)

    def test_has_timestamp_mixin(self):
        from app.models.cohorte import Cohorte

        assert issubclass(Cohorte, TimestampMixin)

    def test_has_tenant_mixin(self):
        from app.models.cohorte import Cohorte

        assert issubclass(Cohorte, TenantMixin)

    def test_tablename_is_cohortes(self):
        from app.models.cohorte import Cohorte

        assert Cohorte.__tablename__ == "cohortes"

    def test_has_carrera_id(self):
        from app.models.cohorte import Cohorte

        assert hasattr(Cohorte, "carrera_id")

    def test_has_nombre(self):
        from app.models.cohorte import Cohorte

        assert hasattr(Cohorte, "nombre")

    def test_has_anio(self):
        from app.models.cohorte import Cohorte

        assert hasattr(Cohorte, "anio")

    def test_anio_is_integer(self):
        from app.models.cohorte import Cohorte

        ann = Cohorte.__annotations__["anio"]
        assert "int" in str(ann)

    def test_has_vig_desde(self):
        from app.models.cohorte import Cohorte

        assert hasattr(Cohorte, "vig_desde")

    def test_has_vig_hasta(self):
        from app.models.cohorte import Cohorte

        assert hasattr(Cohorte, "vig_hasta")

    def test_estado_uses_estado_academico(self):
        from app.models.cohorte import Cohorte

        ann = Cohorte.__annotations__["estado"]
        assert "EstadoAcademico" in str(ann)

    def test_unique_constraint_on_tenant_carrera_nombre(self):
        from app.models.cohorte import Cohorte

        uq = Cohorte.__table_args__
        has_uq = False
        for arg in uq:
            if hasattr(arg, "columns"):
                col_names = [str(c) for c in arg.columns]
                if all(c in str(arg) for c in ["tenant_id", "carrera_id", "nombre"]):
                    has_uq = True
        assert has_uq


class TestMateriaModel:
    """Materia model — subject catalog."""

    def test_extends_app_model(self):
        from app.models.materia import Materia

        assert issubclass(Materia, AppModel)

    def test_has_timestamp_mixin(self):
        from app.models.materia import Materia

        assert issubclass(Materia, TimestampMixin)

    def test_has_tenant_mixin(self):
        from app.models.materia import Materia

        assert issubclass(Materia, TenantMixin)

    def test_tablename_is_materias(self):
        from app.models.materia import Materia

        assert Materia.__tablename__ == "materias"

    def test_has_codigo(self):
        from app.models.materia import Materia

        assert hasattr(Materia, "codigo")

    def test_codigo_is_string(self):
        from app.models.materia import Materia

        ann = Materia.__annotations__["codigo"]
        assert "str" in str(ann)

    def test_has_nombre(self):
        from app.models.materia import Materia

        assert hasattr(Materia, "nombre")

    def test_estado_uses_estado_academico(self):
        from app.models.materia import Materia

        ann = Materia.__annotations__["estado"]
        assert "EstadoAcademico" in str(ann)

    def test_tenant_id_not_nullable(self):
        from app.models.materia import Materia

        assert hasattr(Materia, "tenant_id")

    def test_unique_constraint_on_tenant_codigo(self):
        from app.models.materia import Materia

        uq = Materia.__table_args__
        has_uq = False
        for arg in uq:
            if hasattr(arg, "columns"):
                if "tenant_id" in str(arg) and "codigo" in str(arg):
                    has_uq = True
        assert has_uq


class TestProgramaMateriaModel:
    """ProgramaMateria model — syllabus document registry."""

    def test_extends_app_model(self):
        from app.models.programa_materia import ProgramaMateria

        assert issubclass(ProgramaMateria, AppModel)

    def test_does_not_have_audit_mixin(self):
        from app.models.programa_materia import ProgramaMateria

        assert not issubclass(ProgramaMateria, AuditMixin)

    def test_has_tenant_mixin(self):
        from app.models.programa_materia import ProgramaMateria

        assert issubclass(ProgramaMateria, TenantMixin)

    def test_tablename_is_programas_materia(self):
        from app.models.programa_materia import ProgramaMateria

        assert ProgramaMateria.__tablename__ == "programas_materia"

    def test_has_materia_id(self):
        from app.models.programa_materia import ProgramaMateria

        assert hasattr(ProgramaMateria, "materia_id")

    def test_has_carrera_id(self):
        from app.models.programa_materia import ProgramaMateria

        assert hasattr(ProgramaMateria, "carrera_id")

    def test_has_cohorte_id(self):
        from app.models.programa_materia import ProgramaMateria

        assert hasattr(ProgramaMateria, "cohorte_id")

    def test_has_titulo(self):
        from app.models.programa_materia import ProgramaMateria

        assert hasattr(ProgramaMateria, "titulo")

    def test_has_referencia_archivo(self):
        from app.models.programa_materia import ProgramaMateria

        assert hasattr(ProgramaMateria, "referencia_archivo")

    def test_has_cargado_at(self):
        from app.models.programa_materia import ProgramaMateria

        assert hasattr(ProgramaMateria, "cargado_at")
