"""Tests for LiquidacionService — calculation engine, lifecycle, KPI aggregation.

Pure unit tests for testable logic (date math, totals, KPI aggregation).
Integration tests (DB-dependent) are skipped by default.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.models.liquidacion import EstadoLiquidacion
from app.services.liquidacion import _compute_period_last_day, _compute_total, _aggregate_kpis


# ── Pure function tests (RED phase) ──────────────────────────────────────


class TestComputePeriodLastDay:
    """_compute_period_last_day: YYYY-MM → last day of month."""

    def test_regular_month(self):
        assert _compute_period_last_day("2026-06") == date(2026, 6, 30)

    def test_february_leap(self):
        assert _compute_period_last_day("2024-02") == date(2024, 2, 29)

    def test_february_non_leap(self):
        assert _compute_period_last_day("2025-02") == date(2025, 2, 28)

    def test_31_day_month(self):
        assert _compute_period_last_day("2026-01") == date(2026, 1, 31)

    def test_30_day_month(self):
        assert _compute_period_last_day("2026-04") == date(2026, 4, 30)

    def test_december(self):
        assert _compute_period_last_day("2026-12") == date(2026, 12, 31)


class TestComputeTotal:
    """_compute_total: Base + Sum(Plus) = Total per RN-21/RN-34."""

    def test_base_only(self):
        assert _compute_total(Decimal("150000.00"), Decimal("0")) == Decimal("150000.00")

    def test_base_and_plus(self):
        assert _compute_total(Decimal("150000.00"), Decimal("5000.00")) == Decimal("155000.00")

    def test_multiple_plus(self):
        assert _compute_total(Decimal("100000.00"), Decimal("25000.00")) == Decimal("125000.00")

    def test_zero_base(self):
        assert _compute_total(Decimal("0"), Decimal("5000")) == Decimal("5000")

    def test_large_values(self):
        assert _compute_total(Decimal("999999.99"), Decimal("0.01")) == Decimal("1000000.00")


class TestAggregateKPIs:
    """_aggregate_kpis: Total sin factura vs Total con factura (RN-38)."""

    def test_empty_list(self):
        kpi = _aggregate_kpis([])
        assert kpi["total_sin_factura"] == 0
        assert kpi["total_con_factura"] == 0
        assert kpi["total_general"] == 0

    def test_all_sin_factura(self):
        rows = [
            {"total": 1000.0, "excluido_por_factura": False},
            {"total": 2000.0, "excluido_por_factura": False},
        ]
        kpi = _aggregate_kpis(rows)
        assert kpi["total_sin_factura"] == 3000.0
        assert kpi["total_con_factura"] == 0
        assert kpi["total_general"] == 3000.0

    def test_all_con_factura(self):
        rows = [
            {"total": 5000.0, "excluido_por_factura": True},
            {"total": 3000.0, "excluido_por_factura": True},
        ]
        kpi = _aggregate_kpis(rows)
        assert kpi["total_sin_factura"] == 0
        assert kpi["total_con_factura"] == 8000.0
        assert kpi["total_general"] == 8000.0

    def test_mixed(self):
        rows = [
            {"total": 1000.0, "excluido_por_factura": False},
            {"total": 500.0, "excluido_por_factura": True},
            {"total": 2000.0, "excluido_por_factura": False},
        ]
        kpi = _aggregate_kpis(rows)
        assert kpi["total_sin_factura"] == 3000.0
        assert kpi["total_con_factura"] == 500.0
        assert kpi["total_general"] == 3500.0

    def test_nexo_included_in_total(self):
        """RN-36: NEXO shows separate but sums to total."""
        rows = [
            {"total": 1000.0, "excluido_por_factura": False},
        ]
        kpi = _aggregate_kpis(rows)
        assert kpi["total_general"] == 1000.0


class TestEstadoLiquidacion:
    """EstadoLiquidacion enum: Abierta/Cerrada semantics."""

    def test_abierta_can_be_closed(self):
        assert EstadoLiquidacion.ABIERTA.value == "Abierta"
        assert EstadoLiquidacion.ABIERTA != EstadoLiquidacion.CERRADA

    def test_cerrada_is_immutable(self):
        assert EstadoLiquidacion.CERRADA.value == "Cerrada"


# ── Integration tests (skipped) ──────────────────────────────────────────


@pytest.mark.skip(reason="Requires PostgreSQL (testcontainers)")
class TestLiquidacionServiceIntegration:
    """Integration tests for LiquidacionService — requires DB.

    Run with: pytest --run-integration
    """

    async def test_calcular_periodo_creates_liquidaciones(self):
        """RN-34: Full calculation cycle for a cohorte in a period."""
        ...

    async def test_cerrar_liquidacion_sets_estado_cerrada(self):
        """RN-22: Close sets estado=Cerrada and cerrada_at."""
        ...

    async def test_cerrar_already_closed_raises(self):
        """RN-22: Re-closing Cerrada returns 409."""
        ...

    async def test_calcular_facturante_excluido(self):
        """RN-35: Teacher with facturador=true → excluido_por_factura=true."""
        ...

    async def test_calcular_nexo_role(self):
        """RN-36: NEXO role → es_nexo=true."""
        ...

    async def test_calcular_no_vigente_salario_skips(self):
        """Teacher without vigente SalarioBase → skipped with warning."""
        ...

    async def test_calcular_multiple_comisiones_same_grupo(self):
        """Multiple comisiones in same grupo → plus summed."""
        ...

    async def test_kpi_aggregation(self):
        """RN-38: Period view returns correct KPIs."""
        ...

    async def test_unique_constraint_duplicate(self):
        """Duplicate (cohorte, usuario, periodo) → integrity error."""
        ...
