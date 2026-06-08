"""Tests for Tenant model — multi-tenant root entity."""

import pytest
from app.models.mixins import TimestampMixin
from app.models.tenant import Tenant
from app.models.base import AppModel


class TestTenantModel:
    """Tenant model structure and defaults."""

    def test_extends_app_model(self):
        """Tenant should inherit from AppModel (has UUID id)."""
        assert issubclass(Tenant, AppModel)

    def test_has_timestamp_mixin(self):
        """Tenant should have created_at and updated_at."""
        assert issubclass(Tenant, TimestampMixin)

    def test_tablename_is_tenants(self):
        """Tenant should use explicit tablename 'tenants'."""
        assert Tenant.__tablename__ == "tenants"

    def test_has_nombre(self):
        """Tenant should have a nombre column."""
        assert hasattr(Tenant, "nombre")

    def test_nombre_is_string(self):
        """nombre should accept string values."""
        annotations = Tenant.__annotations__
        assert "nombre" in annotations

    def test_has_configuracion(self):
        """Tenant should have a configuracion column (JSONB)."""
        assert hasattr(Tenant, "configuracion")

    def test_has_activo(self):
        """Tenant should have an activo column."""
        assert hasattr(Tenant, "activo")

    def test_does_not_have_tenant_id(self):
        """Tenant (the root entity) should NOT have tenant_id."""
        assert not hasattr(Tenant, "tenant_id")

    def test_does_not_have_estado(self):
        """Tenant should not have estado (not using AuditMixin)."""
        assert not hasattr(Tenant, "estado")
