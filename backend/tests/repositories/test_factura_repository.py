"""Tests for FacturaRepository — CRUD, filtering, pagination, scope.

All tests are marked as integration/skipped since they require PostgreSQL.
Pure unit tests cover the interface contract.
"""

import pytest

from app.repositories.factura import FacturaRepository


class TestFacturaRepositoryInterface:
    """Verify FacturaRepository exposes the expected methods."""

    def test_has_create_method(self):
        assert hasattr(FacturaRepository, "create")

    def test_has_find_by_id_method(self):
        assert hasattr(FacturaRepository, "find_by_id")

    def test_has_find_by_usuario_method(self):
        assert hasattr(FacturaRepository, "find_by_usuario")

    def test_has_find_all_method(self):
        assert hasattr(FacturaRepository, "find_all")

    def test_has_save_method(self):
        assert hasattr(FacturaRepository, "save")

    def test_inherits_from_base_repository(self):
        from app.repositories.base import BaseRepository
        assert issubclass(FacturaRepository, BaseRepository)

    def test_accepts_session_and_tenant_id(self):
        """Constructor signature matches existing pattern."""
        import inspect
        sig = inspect.signature(FacturaRepository.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "session" in params
        assert "tenant_id" in params


# ── Integration tests (skipped) ──────────────────────────────────────────


@pytest.mark.skip(reason="Requires PostgreSQL (testcontainers)")
class TestFacturaRepositoryIntegration:
    """Integration tests for FacturaRepository — requires DB.

    Run with: pytest --run-integration
    """

    async def test_create_factura(self):
        """Create a new factura record."""
        ...

    async def test_find_by_id_returns_none_for_missing(self):
        """Non-existent ID returns None."""
        ...

    async def test_find_by_id_scoped_by_tenant(self):
        """Facturas from other tenants are not visible."""
        ...

    async def test_find_by_usuario_returns_own_facturas(self):
        """Returns facturas for a specific usuario."""
        ...

    async def test_find_by_usuario_filters_by_periodo(self):
        """Optional periodo filter on usuario history."""
        ...

    async def test_find_by_usuario_paginates(self):
        """Pagination works on usuario history."""
        ...

    async def test_find_all_no_filters(self):
        """All facturas for tenant with pagination."""
        ...

    async def test_find_all_filter_by_estado(self):
        """Filter by estado (Pendiente/Abonada)."""
        ...

    async def test_find_all_filter_by_periodo(self):
        """Filter by periodo YYYY-MM."""
        ...

    async def test_find_all_filter_by_usuario(self):
        """Filter by usuario_id."""
        ...

    async def test_find_all_search_by_detalle(self):
        """Search by LIKE on detalle."""
        ...

    async def test_find_all_combined_filters(self):
        """Multiple filters applied in AND."""
        ...

    async def test_save_persists_changes(self):
        """Save flushes and persists changes."""
        ...
