"""Unit tests for TeamManagementService — pure logic, no DB required.

Tests marked with ``@pytest.mark.integration`` require testcontainers
and are skipped by default.
"""

from datetime import date

import pytest

from app.schemas.team_management import ClonarRequest
from app.services.team_management import _compute_estado_vigencia


class TestComputeEstadoVigencia:
    """Pure function tests for _compute_estado_vigencia (Task 8.1)."""

    def test_vigente_within_range(self):
        assert _compute_estado_vigencia(
            date(2026, 3, 1), date(2026, 12, 31), today=date(2026, 6, 7)
        ) == "Vigente"

    def test_vencida_past_vig_hasta(self):
        assert _compute_estado_vigencia(
            date(2025, 3, 1), date(2025, 12, 31), today=date(2026, 6, 7)
        ) == "Vencida"

    def test_pendiente_future_vig_desde(self):
        assert _compute_estado_vigencia(
            date(2026, 9, 1), date(2027, 3, 1), today=date(2026, 6, 7)
        ) == "Pendiente"

    def test_vigente_null_vig_hasta(self):
        assert _compute_estado_vigencia(
            date(2026, 3, 1), None, today=date(2026, 6, 7)
        ) == "Vigente"

    def test_pendiente_null_vig_hasta_future(self):
        assert _compute_estado_vigencia(
            date(2026, 9, 1), None, today=date(2026, 6, 7)
        ) == "Pendiente"

    def test_vigente_on_vig_desde(self):
        assert _compute_estado_vigencia(
            date(2026, 6, 7), date(2026, 12, 31), today=date(2026, 6, 7)
        ) == "Vigente"

    def test_vencida_exactly_next_day(self):
        assert _compute_estado_vigencia(
            date(2025, 1, 1), date(2025, 12, 31), today=date(2026, 1, 1)
        ) == "Vencida"

    def test_vigente_on_vig_hasta_inclusive(self):
        assert _compute_estado_vigencia(
            date(2025, 1, 1), date(2025, 12, 31), today=date(2025, 12, 31)
        ) == "Vigente"

    def test_default_today(self):
        """When no today is passed, uses date.today()."""
        result = _compute_estado_vigencia(
            date(2020, 1, 1), date(2020, 12, 31)
        )
        # Today is 2026-06-08, so this should be Vencida
        assert result == "Vencida"


# ── Task 8.3: ClonarRequest schema validation (already in schema tests) ─
# ── Task 8.5: clone with matching source/destination → 422 ─────────────


class TestClonarRequestValidation:
    """ClonarRequest validation — source != destination (Task 8.3)."""

    def test_valid_different_contexts(self):
        req = ClonarRequest(
            origen_materia_id="a",
            origen_carrera_id="b",
            origen_cohorte_id="c",
            destino_materia_id="d",
            destino_carrera_id="e",
            destino_cohorte_id="f",
        )
        assert req.origen_materia_id != req.destino_materia_id

    def test_identical_contexts_raises(self):
        with pytest.raises(ValueError) as exc:
            ClonarRequest(
                origen_materia_id="x",
                origen_carrera_id="y",
                origen_cohorte_id="z",
                destino_materia_id="x",
                destino_carrera_id="y",
                destino_cohorte_id="z",
            )
        assert "differ" in str(exc.value).lower()


# ── Task 8.6: _validate_academic_context with cross-tenant FKs ──────────
# NOTE: This test requires a real DB (testcontainers). See integration tests.


@pytest.mark.skip(reason="Requires PostgreSQL (testcontainers)")
class TestValidateAcademicContext:
    """_validate_academic_context — requires DB, tested in integration."""

    async def test_cross_tenant_reference_returns_404(self):
        """Placeholder: see test_team_management_api.py for integration tests."""
        pass


# ── Task 8.4: asignacion_masiva with non-existent usuario ───────────────
# NOTE: Requires real DB. Integration tests cover this case.


@pytest.mark.skip(reason="Requires PostgreSQL (testcontainers)")
class TestAsignacionMasivaRollback:
    """asignacion_masiva rollback — requires DB, tested in integration."""

    async def test_nonexistent_usuario_rolls_back(self):
        """Placeholder: see test_team_management_api.py test 9.8."""
        pass
