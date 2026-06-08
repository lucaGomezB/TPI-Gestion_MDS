"""Tests for salary grid Pydantic schemas (C-18 Tasks 4.1)."""

from datetime import date

import pytest
from pydantic import ValidationError


class TestSalarioBaseCreate:
    """SalarioBaseCreate schema validation."""

    def test_valid_minimal(self):
        from app.schemas.grilla_salarial import SalarioBaseCreate

        schema = SalarioBaseCreate(rol="PROFESOR", monto=150000.00, desde="2026-01-01")
        assert schema.rol == "PROFESOR"
        assert schema.monto == 150000.00
        assert schema.desde == date(2026, 1, 1)
        assert schema.hasta is None

    def test_valid_with_hasta(self):
        from app.schemas.grilla_salarial import SalarioBaseCreate

        schema = SalarioBaseCreate(
            rol="COORDINADOR",
            monto=200000.00,
            desde="2026-01-01",
            hasta="2026-12-31",
        )
        assert schema.hasta == date(2026, 12, 31)

    def test_rejects_invalid_rol(self):
        from app.schemas.grilla_salarial import SalarioBaseCreate

        with pytest.raises(ValidationError):
            SalarioBaseCreate(rol="INEXISTENTE", monto=1000.00, desde="2026-01-01")

    def test_rejects_empty_rol(self):
        from app.schemas.grilla_salarial import SalarioBaseCreate

        with pytest.raises(ValidationError):
            SalarioBaseCreate(monto=1000.00, desde="2026-01-01")

    def test_rejects_zero_monto(self):
        from app.schemas.grilla_salarial import SalarioBaseCreate

        with pytest.raises(ValidationError):
            SalarioBaseCreate(rol="PROFESOR", monto=0, desde="2026-01-01")

    def test_rejects_negative_monto(self):
        from app.schemas.grilla_salarial import SalarioBaseCreate

        with pytest.raises(ValidationError):
            SalarioBaseCreate(rol="PROFESOR", monto=-1000, desde="2026-01-01")

    def test_rejects_hasta_before_desde(self):
        from app.schemas.grilla_salarial import SalarioBaseCreate

        with pytest.raises(ValidationError):
            SalarioBaseCreate(
                rol="PROFESOR",
                monto=100000.00,
                desde="2026-12-31",
                hasta="2026-01-01",
            )

    def test_extra_field_forbidden(self):
        from app.schemas.grilla_salarial import SalarioBaseCreate

        with pytest.raises(ValidationError):
            SalarioBaseCreate(
                rol="PROFESOR",
                monto=100000.00,
                desde="2026-01-01",
                extra_field="invalid",
            )

    def test_rejects_unknown_roles(self):
        from app.schemas.grilla_salarial import SalarioBaseCreate

        for invalid_rol in ["ADMIN", "ALUMNO", "DIRECTOR", ""]:
            with pytest.raises(ValidationError):
                SalarioBaseCreate(rol=invalid_rol, monto=1000.00, desde="2026-01-01")


class TestSalarioBaseUpdate:
    """SalarioBaseUpdate schema validation."""

    def test_partial_update_allowed(self):
        from app.schemas.grilla_salarial import SalarioBaseUpdate

        schema = SalarioBaseUpdate(monto=160000.00)
        assert schema.monto == 160000.00
        assert schema.rol is None

    def test_extra_field_forbidden(self):
        from app.schemas.grilla_salarial import SalarioBaseUpdate

        with pytest.raises(ValidationError):
            SalarioBaseUpdate(monto=160000.00, extra="bad")

    def test_rejects_hasta_before_desde(self):
        from app.schemas.grilla_salarial import SalarioBaseUpdate

        with pytest.raises(ValidationError):
            SalarioBaseUpdate(desde="2026-12-31", hasta="2026-01-01")


class TestSalarioBaseResponse:
    """SalarioBaseResponse schema."""

    def test_includes_all_fields(self):
        from app.schemas.grilla_salarial import SalarioBaseResponse

        schema = SalarioBaseResponse(
            id="some-uuid",
            tenant_id="tenant-uuid",
            rol="PROFESOR",
            monto=150000.00,
            desde="2026-01-01",
            hasta=None,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        assert schema.id == "some-uuid"
        assert schema.tenant_id == "tenant-uuid"
        assert schema.monto == 150000.00

    def test_extra_field_forbidden(self):
        from app.schemas.grilla_salarial import SalarioBaseResponse

        with pytest.raises(ValidationError):
            SalarioBaseResponse(
                id="uuid",
                tenant_id="uuid",
                rol="PROFESOR",
                monto=1000.00,
                desde="2026-01-01",
                created_at="2026-01-01T00:00:00Z",
                updated_at="2026-01-01T00:00:00Z",
                extra="bad",
            )


class TestSalarioPlusCreate:
    """SalarioPlusCreate schema validation."""

    def test_valid(self):
        from app.schemas.grilla_salarial import SalarioPlusCreate

        schema = SalarioPlusCreate(
            grupo="PROG",
            rol="PROFESOR",
            descripcion="Plus Programacion",
            monto=5000.00,
            desde="2026-01-01",
        )
        assert schema.grupo == "PROG"
        assert schema.rol == "PROFESOR"
        assert schema.monto == 5000.00

    def test_rejects_invalid_rol(self):
        from app.schemas.grilla_salarial import SalarioPlusCreate

        with pytest.raises(ValidationError):
            SalarioPlusCreate(
                grupo="PROG",
                rol="ADMIN",
                descripcion="Test",
                monto=1000.00,
                desde="2026-01-01",
            )

    def test_rejects_hasta_before_desde(self):
        from app.schemas.grilla_salarial import SalarioPlusCreate

        with pytest.raises(ValidationError):
            SalarioPlusCreate(
                grupo="PROG",
                rol="PROFESOR",
                descripcion="Test",
                monto=1000.00,
                desde="2026-12-31",
                hasta="2026-01-01",
            )

    def test_extra_field_forbidden(self):
        from app.schemas.grilla_salarial import SalarioPlusCreate

        with pytest.raises(ValidationError):
            SalarioPlusCreate(
                grupo="PROG",
                rol="PROFESOR",
                descripcion="Test",
                monto=1000.00,
                desde="2026-01-01",
                extra="bad",
            )


class TestGrupoMateriaCreate:
    """GrupoMateriaCreate schema validation."""

    def test_valid(self):
        from app.schemas.grilla_salarial import GrupoMateriaCreate

        schema = GrupoMateriaCreate(grupo="PROG", descripcion="Programacion")
        assert schema.grupo == "PROG"

    def test_valid_without_descripcion(self):
        from app.schemas.grilla_salarial import GrupoMateriaCreate

        schema = GrupoMateriaCreate(grupo="PROG")
        assert schema.descripcion is None

    def test_rejects_empty_grupo(self):
        from app.schemas.grilla_salarial import GrupoMateriaCreate

        with pytest.raises(ValidationError):
            GrupoMateriaCreate(grupo="")

    def test_extra_field_forbidden(self):
        from app.schemas.grilla_salarial import GrupoMateriaCreate

        with pytest.raises(ValidationError):
            GrupoMateriaCreate(grupo="PROG", extra="bad")


class TestGrupoMateriaUpdate:
    """GrupoMateriaUpdate schema validation."""

    def test_partial_update(self):
        from app.schemas.grilla_salarial import GrupoMateriaUpdate

        schema = GrupoMateriaUpdate(descripcion="Nueva descripcion")
        assert schema.descripcion == "Nueva descripcion"

    def test_extra_field_forbidden(self):
        from app.schemas.grilla_salarial import GrupoMateriaUpdate

        with pytest.raises(ValidationError):
            GrupoMateriaUpdate(descripcion="Test", extra="bad")
