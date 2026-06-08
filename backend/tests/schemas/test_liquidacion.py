"""Tests for Liquidacion Pydantic schemas — validation, extra='forbid', field rules.

Covers all schemas: LiquidacionCreate, LiquidacionResponse,
LiquidacionDetailResponse, LiquidacionCerrarResponse, LiquidacionListResponse.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.liquidacion import (
    LiquidacionCreate,
    LiquidacionDetailResponse,
    LiquidacionListResponse,
    LiquidacionResponse,
    LiquidacionKPI,
)


class TestLiquidacionCreate:
    """LiquidacionCreate — internal create schema validation."""

    def test_valid_create(self):
        data = LiquidacionCreate(
            cohorte_id="c1",
            periodo="2026-06",
            usuario_id="u1",
            rol="PROFESOR",
            comisiones=["PROG-A", "PROG-B"],
            monto_base=150000.00,
            monto_plus=5000.00,
            total=155000.00,
            es_nexo=False,
            excluido_por_factura=False,
        )
        assert data.total == 155000.00

    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            LiquidacionCreate(
                cohorte_id="c1",
                periodo="2026-06",
                usuario_id="u1",
                rol="PROFESOR",
                comisiones=[],
                monto_base=100.0,
                monto_plus=0.0,
                total=100.0,
                es_nexo=False,
                excluido_por_factura=False,
                extra_field="should not exist",
            )

    def test_monto_base_required(self):
        with pytest.raises(ValidationError):
            LiquidacionCreate(
                cohorte_id="c1",
                periodo="2026-06",
                usuario_id="u1",
                rol="PROFESOR",
                comisiones=[],
                monto_plus=0.0,
                total=0.0,
                es_nexo=False,
                excluido_por_factura=False,
            )


class TestLiquidacionResponse:
    """LiquidacionResponse — API response schema."""

    def test_valid_response(self):
        data = LiquidacionResponse(
            id="liq-1",
            tenant_id="t1",
            cohorte_id="c1",
            periodo="2026-06",
            usuario_id="u1",
            rol="PROFESOR",
            comisiones=["PROG-A"],
            monto_base=150000.00,
            monto_plus=5000.00,
            total=155000.00,
            es_nexo=False,
            excluido_por_factura=False,
            estado="Abierta",
            created_at="2026-06-08T00:00:00+00:00",
            cerrada_at=None,
        )
        assert data.id == "liq-1"
        assert data.total == 155000.00

    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            LiquidacionResponse(
                id="x",
                tenant_id="t",
                cohorte_id="c",
                periodo="2026-06",
                usuario_id="u",
                rol="PROFESOR",
                comisiones=[],
                monto_base=100.0,
                monto_plus=0.0,
                total=100.0,
                es_nexo=False,
                excluido_por_factura=False,
                estado="Abierta",
                created_at="now",
                extra="bad",
            )


class TestLiquidacionKPI:
    """KPI aggregation schema validation."""

    def test_valid_kpi(self):
        kpi = LiquidacionKPI(
            total_sin_factura=1000000.00,
            total_con_factura=500000.00,
            total_general=1500000.00,
        )
        assert kpi.total_general == kpi.total_sin_factura + kpi.total_con_factura

    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            LiquidacionKPI(
                total_sin_factura=0.0,
                total_con_factura=0.0,
                total_general=0.0,
                extra=True,
            )


class TestLiquidacionListResponse:
    """List response schema validation."""

    def test_valid_list_response(self):
        resp = LiquidacionListResponse(
            items=[],
            kpis=LiquidacionKPI(
                total_sin_factura=0.0, total_con_factura=0.0, total_general=0.0
            ),
            total=0,
            page=1,
            page_size=50,
        )
        assert resp.total == 0
        assert resp.kpis.total_general == 0.0

    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            LiquidacionListResponse(
                items=[],
                kpis={"total_sin_factura": 0, "total_con_factura": 0, "total_general": 0},
                total=0,
                page=1,
                page_size=50,
                bad=True,
            )


class TestLiquidacionDetailResponse:
    """Detail response with desglose fields."""

    def test_valid_detail(self):
        detail = LiquidacionDetailResponse(
            id="liq-1",
            tenant_id="t1",
            cohorte_id="c1",
            periodo="2026-06",
            usuario_id="u1",
            rol="PROFESOR",
            comisiones=["PROG-A"],
            monto_base=150000.00,
            monto_plus=5000.00,
            total=155000.00,
            es_nexo=False,
            excluido_por_factura=False,
            estado="Abierta",
            created_at="2026-06-08T00:00:00+00:00",
            cerrada_at=None,
            desglose_base={"rol": "PROFESOR", "monto": 150000.00},
            desglose_plus=[{"grupo": "PROG", "rol": "PROFESOR", "monto": 5000.00, "descripcion": "Plus PROG"}],
        )
        assert detail.desglose_base["rol"] == "PROFESOR"
        assert len(detail.desglose_plus) == 1
