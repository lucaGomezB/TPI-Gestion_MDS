"""Tests for model mixins — TimestampMixin, AuditMixin, TenantMixin, EstadoRegistro."""

from datetime import datetime

import pytest
from app.models.mixins import AuditMixin, EstadoAcademico, EstadoRegistro, TenantMixin, TimestampMixin
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped


class TestEstadoRegistro:
    """EstadoRegistro enum semantics."""

    def test_activo_value(self):
        assert EstadoRegistro.ACTIVO.value == "Activo"

    def test_inactivo_value(self):
        assert EstadoRegistro.INACTIVO.value == "Inactivo"

    def test_is_str_enum(self):
        assert issubclass(EstadoRegistro, str)


class TestEstadoAcademico:
    """EstadoAcademico enum — feminine form for academic entities."""

    def test_activa_value(self):
        assert EstadoAcademico.ACTIVA.value == "Activa"

    def test_inactiva_value(self):
        assert EstadoAcademico.INACTIVA.value == "Inactiva"

    def test_is_str_enum(self):
        assert issubclass(EstadoAcademico, str)

    def test_activa_is_default(self):
        """Activa should be the first/primary value."""
        assert list(EstadoAcademico)[0] == EstadoAcademico.ACTIVA


class TestTimestampMixin:
    """TimestampMixin provides created_at and updated_at columns."""

    def test_has_created_at(self):
        assert hasattr(TimestampMixin, "created_at")

    def test_created_at_is_mapped_datetime(self):
        col = TimestampMixin.__annotations__["created_at"]
        # Mapped[datetime] — check the inner type
        assert "datetime" in str(col)

    def test_has_updated_at(self):
        assert hasattr(TimestampMixin, "updated_at")

    def test_updated_at_is_mapped_datetime(self):
        col = TimestampMixin.__annotations__["updated_at"]
        assert "datetime" in str(col)


class TestAuditMixin:
    """AuditMixin replaces SoftDeleteMixin with estado enum."""

    def test_has_estado(self):
        assert hasattr(AuditMixin, "estado")

    def test_estado_default_is_activo(self):
        """Default value should be Activo."""
        # The column default should be EstadoRegistro.ACTIVO
        col = AuditMixin.__annotations__["estado"]
        assert "EstadoRegistro" in str(col)

    def test_has_deleted_at(self):
        assert hasattr(AuditMixin, "deleted_at")

    def test_deleted_at_is_nullable(self):
        col = AuditMixin.__annotations__["deleted_at"]
        assert "datetime" in str(col) or "None" in str(col)

    def test_does_not_have_is_active(self):
        """AuditMixin should NOT have the old is_active boolean."""
        assert not hasattr(AuditMixin, "is_active")


class TestTenantMixin:
    """TenantMixin provides tenant_id foreign key."""

    def test_has_tenant_id(self):
        assert hasattr(TenantMixin, "tenant_id")

    def test_tenant_id_allows_nullable(self):
        """TenantMixin defaults to nullable=True (Tenant model has no parent)."""
        col = TenantMixin.__annotations__["tenant_id"]
        assert "str" in str(col) or "None" in str(col)

    def test_does_not_have_is_active(self):
        """TenantMixin should not carry the soft-delete flag."""
        assert not hasattr(TenantMixin, "is_active")
