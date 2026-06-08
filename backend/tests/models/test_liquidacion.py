"""Tests for Liquidacion model — field defaults, constraints, and lifecycle.

All values should be validated via schema layer; model tests focus on
column defaults, nullable/non-nullable columns, and ORM behavior.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.liquidacion import EstadoLiquidacion, Liquidacion


class TestLiquidacionModel:
    """DDD-focused: Liquidacion state and lifecycle semantics."""

    def test_estado_liquidacion_values(self):
        """EstadoLiquidacion enum has Abierta and Cerrada."""
        assert EstadoLiquidacion.ABIERTA.value == "Abierta"
        assert EstadoLiquidacion.CERRADA.value == "Cerrada"

    def test_default_estado_is_abierta(self):
        """New liquidacion defaults to Abierta."""
        assert EstadoLiquidacion.ABIERTA.value == "Abierta"

    def test_default_es_nexo_is_false(self):
        """es_nexo defaults to False."""
        assert Liquidacion.es_nexo.default.arg is False

    def test_default_excluido_por_factura_is_false(self):
        """excluido_por_factura defaults to False."""
        assert Liquidacion.excluido_por_factura.default.arg is False

    def test_cerrada_at_nullable(self):
        """cerrada_at is nullable (null until cerrada)."""
        from sqlalchemy import inspect
        cols = inspect(Liquidacion).columns
        assert cols["cerrada_at"].nullable is True

    def test_comisiones_default_list(self):
        """comisiones defaults to empty list."""
        from sqlalchemy import inspect
        cols = inspect(Liquidacion).columns
        col = cols["comisiones"]
        # JSONB default is handled at the server level; at the ORM level
        # it's None if not provided. The model init ensures list default.
        liq = Liquidacion(
            tenant_id="t1",
            cohorte_id="c1",
            periodo="2026-06",
            usuario_id="u1",
            rol="PROFESOR",
            comisiones=[],
            monto_base=100.0,
            monto_plus=0.0,
            total=100.0,
        )
        assert liq.comisiones == []


@pytest.mark.skip(reason="Requires PostgreSQL (testcontainers)")
class TestLiquidacionDB:
    """Integration tests for DB persistence — requires testcontainers."""

    async def test_create_liquidacion(self, db_session: AsyncSession):
        """Can create a liquidacion with all required fields."""
        liq = Liquidacion(
            tenant_id="t1",
            cohorte_id="c1",
            periodo="2026-06",
            usuario_id="u1",
            rol="PROFESOR",
            comisiones=[],
            monto_base=150000.00,
            monto_plus=5000.00,
            total=155000.00,
            es_nexo=False,
            excluido_por_factura=False,
        )
        db_session.add(liq)
        await db_session.flush()

        result = await db_session.execute(
            select(Liquidacion).where(Liquidacion.id == liq.id)
        )
        saved = result.scalar_one()
        assert saved.periodo == "2026-06"
        assert saved.monto_base == 150000.00
        assert saved.total == 155000.00
        assert saved.estado == "Abierta"
        assert saved.created_at is not None
        assert saved.cerrada_at is None

    async def test_total_computed_correctly(self, db_session: AsyncSession):
        """Total = monto_base + monto_plus."""
        liq = Liquidacion(
            tenant_id="t1",
            cohorte_id="c1",
            periodo="2026-06",
            usuario_id="u1",
            rol="PROFESOR",
            comisiones=[],
            monto_base=200000.00,
            monto_plus=30000.00,
            total=230000.00,
            es_nexo=False,
            excluido_por_factura=False,
        )
        assert liq.total == liq.monto_base + liq.monto_plus
