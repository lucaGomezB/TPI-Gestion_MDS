"""Tests for academic structure Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.academic_structure import (
    CarreraCreate,
    CarreraResponse,
    CarreraUpdate,
    CohorteCreate,
    CohorteUpdate,
    MateriaCreate,
    MateriaResponse,
    MateriaUpdate,
)


class TestCarreraCreate:
    """CarreraCreate schema — codigo uppercasing and validation."""

    def test_lowercase_codigo_is_uppercased(self):
        """Lowercase codigo should be automatically uppercased."""
        data = CarreraCreate(codigo="tupad", nombre="Test")
        assert data.codigo == "TUPAD"

    def test_mixed_case_codigo_is_uppercased(self):
        """Mixed case codigo should be uppercased."""
        data = CarreraCreate(codigo="Prog_I", nombre="Test")
        assert data.codigo == "PROG_I"

    def test_codigo_with_underscores_is_valid(self):
        """Codigo with underscores should be valid."""
        data = CarreraCreate(codigo="PROG_I_2025", nombre="Test")
        assert data.codigo == "PROG_I_2025"

    def test_codigo_with_special_chars_raises(self):
        """Codigo with special characters should raise."""
        with pytest.raises(ValidationError):
            CarreraCreate(codigo="PROG@I", nombre="Test")

    def test_codigo_too_long_raises(self):
        """Codigo longer than 20 chars should raise."""
        with pytest.raises(ValidationError):
            CarreraCreate(codigo="A" * 21, nombre="Test")

    def test_empty_codigo_raises(self):
        with pytest.raises(ValidationError):
            CarreraCreate(codigo="", nombre="Test")

    def test_extra_field_forbidden(self):
        """Extra fields should be rejected."""
        with pytest.raises(ValidationError):
            CarreraCreate(codigo="TEST", nombre="Test", extra_field="x")


class TestCarreraUpdate:
    """CarreraUpdate schema — optional fields, codigo uppercasing."""

    def test_partial_update_nombre_only(self):
        data = CarreraUpdate(nombre="Updated Name")
        assert data.nombre == "Updated Name"
        assert data.codigo is None

    def test_partial_update_estado_only(self):
        data = CarreraUpdate(estado="Inactiva")
        assert data.estado == "Inactiva"

    def test_codigo_uppercased(self):
        data = CarreraUpdate(codigo="newcode")
        assert data.codigo == "NEWCODE"

    def test_invalid_estado_raises(self):
        with pytest.raises(ValidationError):
            CarreraUpdate(estado="Invalid")

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            CarreraUpdate(extra_field="x")


class TestMateriaCreate:
    """MateriaCreate schema — codigo uppercasing."""

    def test_lowercase_codigo_uppercased(self):
        data = MateriaCreate(codigo="prog_i", nombre="Programación I")
        assert data.codigo == "PROG_I"

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            MateriaCreate(codigo="TEST", nombre="Test", extra_field="x")


class TestCohorteCreate:
    """CohorteCreate schema — date range validation."""

    def test_valid_date_range(self):
        data = CohorteCreate(
            carrera_id="uuid-1",
            nombre="MAR-2025",
            anio=2025,
            vig_desde="2025-03-01",
            vig_hasta="2025-12-31",
        )
        assert data.anio == 2025
        assert str(data.vig_desde) == "2025-03-01"
        assert str(data.vig_hasta) == "2025-12-31"

    def test_vig_hasta_nullable(self):
        data = CohorteCreate(
            carrera_id="uuid-1",
            nombre="MAR-2025",
            anio=2025,
            vig_desde="2025-03-01",
        )
        assert data.vig_hasta is None

    def test_vig_desde_after_vig_hasta_raises(self):
        with pytest.raises(ValidationError):
            CohorteCreate(
                carrera_id="uuid-1",
                nombre="MAR-2025",
                anio=2025,
                vig_desde="2025-06-01",
                vig_hasta="2025-03-01",
            )

    def test_anio_bounds(self):
        with pytest.raises(ValidationError):
            CohorteCreate(
                carrera_id="uuid-1",
                nombre="MAR-1899",
                anio=1899,
                vig_desde="1899-03-01",
            )
        with pytest.raises(ValidationError):
            CohorteCreate(
                carrera_id="uuid-1",
                nombre="MAR-2201",
                anio=2201,
                vig_desde="2201-03-01",
            )


class TestCohorteUpdate:
    """CohorteUpdate schema — optional date validation."""

    def test_valid_date_range(self):
        data = CohorteUpdate(vig_desde="2025-03-01", vig_hasta="2025-12-31")
        assert str(data.vig_desde) == "2025-03-01"

    def test_vig_desde_after_vig_hasta_raises(self):
        with pytest.raises(ValidationError):
            CohorteUpdate(vig_desde="2025-06-01", vig_hasta="2025-03-01")


class TestCarreraResponse:
    """CarreraResponse schema — from_attributes mode."""

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            CarreraResponse(
                id="uuid",
                tenant_id="uuid",
                codigo="TEST",
                nombre="Test",
                estado="Activa",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                extra_field="x",
            )


class TestMateriaResponse:
    """MateriaResponse schema — from_attributes mode."""

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            MateriaResponse(
                id="uuid",
                tenant_id="uuid",
                codigo="TEST",
                nombre="Test",
                estado="Activa",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                extra_field="x",
            )
