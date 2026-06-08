"""Tests for team management Pydantic schemas (C-05 Tasks 8.1, 8.2, 8.3)."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.models.types import RolDocente
from app.schemas.team_management import (
    AsignacionCreate,
    AsignacionMasivaRequest,
    AsignacionMasivaResponse,
    AsignacionResponse,
    AsignacionUpdate,
    ClonarRequest,
    ClonarResponse,
    EquipoExportRow,
    VigenciaRequest,
    VigenciaResponse,
)
from app.services.team_management import _compute_estado_vigencia


# ── Task 8.1: _compute_estado_vigencia unit tests ──────────────────────


class TestComputeEstadoVigencia:
    """Unit tests for the vigencia state computation (Task 8.1)."""

    def test_vigente_within_range(self):
        """Today within [vig_desde, vig_hasta] → Vigente."""
        result = _compute_estado_vigencia(
            date(2026, 3, 1), date(2026, 12, 31), today=date(2026, 6, 7)
        )
        assert result == "Vigente"

    def test_vencida_past_vig_hasta(self):
        """Today > vig_hasta → Vencida."""
        result = _compute_estado_vigencia(
            date(2025, 3, 1), date(2025, 12, 31), today=date(2026, 6, 7)
        )
        assert result == "Vencida"

    def test_pendiente_future_vig_desde(self):
        """Today < vig_desde → Pendiente."""
        result = _compute_estado_vigencia(
            date(2026, 9, 1), date(2027, 3, 1), today=date(2026, 6, 7)
        )
        assert result == "Pendiente"

    def test_vigente_null_vig_hasta(self):
        """Null vig_hasta and today >= vig_desde → Vigente."""
        result = _compute_estado_vigencia(
            date(2026, 3, 1), None, today=date(2026, 6, 7)
        )
        assert result == "Vigente"

    def test_pendiente_null_vig_hasta_future(self):
        """Null vig_hasta but today < vig_desde → Pendiente."""
        result = _compute_estado_vigencia(
            date(2026, 9, 1), None, today=date(2026, 6, 7)
        )
        assert result == "Pendiente"

    def test_vigente_on_vig_desde(self):
        """Today == vig_desde → Vigente."""
        result = _compute_estado_vigencia(
            date(2026, 6, 7), date(2026, 12, 31), today=date(2026, 6, 7)
        )
        assert result == "Vigente"

    def test_vencida_on_vig_hasta_plus_one(self):
        """Today == vig_hasta + 1 → Vencida."""
        result = _compute_estado_vigencia(
            date(2025, 1, 1), date(2025, 12, 31), today=date(2026, 1, 1)
        )
        assert result == "Vencida"

    def test_vigente_on_vig_hasta(self):
        """Today == vig_hasta → Vigente (inclusive upper bound)."""
        result = _compute_estado_vigencia(
            date(2025, 1, 1), date(2025, 12, 31), today=date(2025, 12, 31)
        )
        assert result == "Vigente"


# ── Task 8.2: AsignacionCreate schema validation ───────────────────────


class TestAsignacionCreate:
    """AsignacionCreate schema — date range and rol validation."""

    def test_valid_full_assignment(self):
        """Valid PROFESOR assignment with all fields."""
        data = AsignacionCreate(
            usuario_id="uuid-user",
            rol=RolDocente.PROFESOR,
            materia_id="uuid-materia",
            carrera_id="uuid-carrera",
            cohorte_id="uuid-cohorte",
            comisiones=["A", "B"],
            vig_desde="2026-03-01",
            vig_hasta="2026-12-31",
        )
        assert data.usuario_id == "uuid-user"
        assert data.rol == RolDocente.PROFESOR
        assert data.comisiones == ["A", "B"]

    def test_valid_tutor_with_materia(self):
        """TUTOR requires materia_id."""
        data = AsignacionCreate(
            usuario_id="uuid-user",
            rol=RolDocente.TUTOR,
            materia_id="uuid-materia",
            vig_desde="2026-03-01",
        )
        assert data.rol == RolDocente.TUTOR

    def test_valid_tenant_level_admin(self):
        """ADMIN at tenant level (no academic context)."""
        data = AsignacionCreate(
            usuario_id="uuid-user",
            rol=RolDocente.ADMIN,
            vig_desde="2026-03-01",
        )
        assert data.materia_id is None

    def test_valid_finanzas_no_context(self):
        """FINANZAS at tenant level (no academic context)."""
        data = AsignacionCreate(
            usuario_id="uuid-user",
            rol=RolDocente.FINANZAS,
            vig_desde="2026-03-01",
        )
        assert data.rol == RolDocente.FINANZAS

    def test_profesor_without_materia_raises(self):
        """PROFESOR without materia_id should raise."""
        with pytest.raises(ValidationError) as exc:
            AsignacionCreate(
                usuario_id="uuid-user",
                rol=RolDocente.PROFESOR,
                vig_desde="2026-03-01",
            )
        assert "materia_id" in str(exc.value)

    def test_tutor_without_materia_raises(self):
        """TUTOR without materia_id should raise."""
        with pytest.raises(ValidationError) as exc:
            AsignacionCreate(
                usuario_id="uuid-user",
                rol=RolDocente.TUTOR,
                vig_desde="2026-03-01",
            )
        assert "materia_id" in str(exc.value)

    def test_vig_desde_after_vig_hasta_raises(self):
        """vig_desde after vig_hasta should raise."""
        with pytest.raises(ValidationError) as exc:
            AsignacionCreate(
                usuario_id="uuid-user",
                rol=RolDocente.COORDINADOR,
                vig_desde="2026-12-31",
                vig_hasta="2026-03-01",
            )
        assert "vig_desde" in str(exc.value).lower()

    def test_null_vig_hasta_valid(self):
        """Null vig_hasta should be valid."""
        data = AsignacionCreate(
            usuario_id="uuid-user",
            rol=RolDocente.COORDINADOR,
            vig_desde="2026-03-01",
        )
        assert data.vig_hasta is None

    def test_extra_field_forbidden(self):
        """Extra fields should be rejected."""
        with pytest.raises(ValidationError):
            AsignacionCreate(
                usuario_id="uuid-user",
                rol=RolDocente.COORDINADOR,
                vig_desde="2026-03-01",
                extra_field="x",
            )

    def test_invalid_rol_raises(self):
        """Invalid rol string should raise."""
        with pytest.raises(ValidationError):
            AsignacionCreate(
                usuario_id="uuid-user",
                rol="INVALIDO",
                vig_desde="2026-03-01",
            )


class TestAsignacionUpdate:
    """AsignacionUpdate schema — partial update validation."""

    def test_partial_update_rol_only(self):
        data = AsignacionUpdate(rol=RolDocente.TUTOR)
        assert data.rol == RolDocente.TUTOR
        assert data.vig_desde is None

    def test_valid_date_range(self):
        data = AsignacionUpdate(vig_desde="2026-03-01", vig_hasta="2026-12-31")
        assert str(data.vig_desde) == "2026-03-01"

    def test_vig_desde_after_vig_hasta_raises(self):
        with pytest.raises(ValidationError):
            AsignacionUpdate(vig_desde="2026-06-01", vig_hasta="2026-03-01")

    def test_comisiones_update(self):
        data = AsignacionUpdate(comisiones=["A", "C", "D"])
        assert data.comisiones == ["A", "C", "D"]

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            AsignacionUpdate(extra_field="x")


class TestAsignacionResponse:
    """AsignacionResponse schema — from_attributes mode with estado_vigencia."""

    def test_valid_response(self):
        data = AsignacionResponse(
            id="uuid",
            tenant_id="uuid",
            usuario_id="uuid",
            rol="PROFESOR",
            comisiones=["A"],
            vig_desde="2026-03-01",
            vig_hasta="2026-12-31",
            estado_vigencia="Vigente",
            created_at="2026-06-07T00:00:00Z",
            updated_at="2026-06-07T00:00:00Z",
        )
        assert data.estado_vigencia == "Vigente"
        assert data.rol == "PROFESOR"

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            AsignacionResponse(
                id="uuid",
                tenant_id="uuid",
                usuario_id="uuid",
                rol="PROFESOR",
                comisiones=[],
                vig_desde="2026-03-01",
                estado_vigencia="Vigente",
                created_at="2026-06-07T00:00:00Z",
                updated_at="2026-06-07T00:00:00Z",
                extra_field="x",
            )


# ── Task 8.3: ClonarRequest schema validation ──────────────────────────


class TestClonarRequest:
    """ClonarRequest schema — source != destination validation."""

    def test_valid_different_contexts(self):
        data = ClonarRequest(
            origen_materia_id="mat-a",
            origen_carrera_id="car-a",
            origen_cohorte_id="coh-a",
            destino_materia_id="mat-b",
            destino_carrera_id="car-b",
            destino_cohorte_id="coh-b",
        )
        assert data.origen_materia_id == "mat-a"
        assert data.destino_materia_id == "mat-b"

    def test_identical_contexts_raises(self):
        with pytest.raises(ValidationError) as exc:
            ClonarRequest(
                origen_materia_id="mat-a",
                origen_carrera_id="car-a",
                origen_cohorte_id="coh-a",
                destino_materia_id="mat-a",
                destino_carrera_id="car-a",
                destino_cohorte_id="coh-a",
            )
        assert "differ" in str(exc.value).lower()

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            ClonarRequest(
                origen_materia_id="a",
                origen_carrera_id="b",
                origen_cohorte_id="c",
                destino_materia_id="d",
                destino_carrera_id="e",
                destino_cohorte_id="f",
                extra_field="x",
            )


class TestClonarResponse:
    def test_ok(self):
        data = ClonarResponse(clonadas=5)
        assert data.clonadas == 5


# ── Bulk assignment schemas ──────────────────────────────────────────────


class TestAsignacionMasivaRequest:
    """AsignacionMasivaRequest — bulk assignment validation."""

    def test_valid_request(self):
        data = AsignacionMasivaRequest(
            usuario_ids=["u1", "u2", "u3"],
            rol=RolDocente.TUTOR,
            materia_id="mat-a",
            vig_desde="2026-03-01",
            vig_hasta="2026-12-31",
        )
        assert len(data.usuario_ids) == 3

    def test_min_one_usuario(self):
        with pytest.raises(ValidationError):
            AsignacionMasivaRequest(
                usuario_ids=[],
                rol=RolDocente.TUTOR,
                vig_desde="2026-03-01",
            )

    def test_profesor_without_materia_raises(self):
        with pytest.raises(ValidationError):
            AsignacionMasivaRequest(
                usuario_ids=["u1"],
                rol=RolDocente.PROFESOR,
                vig_desde="2026-03-01",
            )

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            AsignacionMasivaRequest(
                usuario_ids=["u1"],
                rol=RolDocente.ADMIN,
                vig_desde="2026-03-01",
                extra_field="x",
            )


class TestAsignacionMasivaResponse:
    def test_ok(self):
        data = AsignacionMasivaResponse(creadas=[], total=0)
        assert data.total == 0


# ── Vigencia schemas ────────────────────────────────────────────────────


class TestVigenciaRequest:
    def test_valid_request(self):
        data = VigenciaRequest(
            materia_id="mat-a",
            vig_desde="2026-03-01",
            vig_hasta="2026-12-31",
        )
        assert str(data.vig_desde) == "2026-03-01"

    def test_invalid_date_range_raises(self):
        with pytest.raises(ValidationError):
            VigenciaRequest(
                materia_id="mat-a",
                vig_desde="2026-12-31",
                vig_hasta="2026-03-01",
            )


class TestVigenciaResponse:
    def test_ok(self):
        data = VigenciaResponse(actualizadas=10)
        assert data.actualizadas == 10


# ── Export schema ───────────────────────────────────────────────────────


class TestEquipoExportRow:
    def test_valid_row(self):
        data = EquipoExportRow(
            docente_nombre="Juan",
            docente_apellidos="Perez",
            docente_email="juan@test.com",
            rol="PROFESOR",
            comisiones="A;B",
            responsable_nombre="Coordinador",
            vig_desde="2026-03-01",
            vig_hasta="2026-12-31",
            estado_vigencia="Vigente",
        )
        assert data.docente_nombre == "Juan"
        assert data.estado_vigencia == "Vigente"

    def test_null_vig_hasta(self):
        data = EquipoExportRow(
            docente_nombre="Ana",
            docente_apellidos="Lopez",
            docente_email="ana@test.com",
            rol="ADMIN",
            comisiones="",
            responsable_nombre="",
            vig_desde="2026-03-01",
            estado_vigencia="Vigente",
        )
        assert data.vig_hasta is None

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            EquipoExportRow(
                docente_nombre="N",
                docente_apellidos="A",
                docente_email="n@t.com",
                rol="PROFESOR",
                comisiones="",
                responsable_nombre="",
                vig_desde="2026-03-01",
                estado_vigencia="V",
                extra_field="x",
            )
