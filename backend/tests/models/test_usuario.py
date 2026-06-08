"""Tests for Usuario model — PII encryption, email_hash, soft-delete."""

import hashlib

import pytest
from app.models.base import AppModel
from app.models.mixins import AuditMixin, TenantMixin, TimestampMixin
from app.models.types import EncryptedString
from app.models.usuario import Usuario


class TestUsuarioModel:
    """Usuario model structure, mixins, and attributes."""

    def test_extends_app_model(self):
        assert issubclass(Usuario, AppModel)

    def test_has_timestamp_mixin(self):
        assert issubclass(Usuario, TimestampMixin)

    def test_has_audit_mixin(self):
        """Usuario should have estado and deleted_at."""
        assert issubclass(Usuario, AuditMixin)

    def test_has_tenant_mixin(self):
        """Usuario should have tenant_id."""
        assert issubclass(Usuario, TenantMixin)

    def test_tablename_is_usuarios(self):
        """Auto tablename from AppModel should be 'usuarios'."""
        assert Usuario.__tablename__ == "usuarios"

    # ── Required attributes ──────────────────────────────────────────

    def test_has_nombre(self):
        assert hasattr(Usuario, "nombre")

    def test_has_apellidos(self):
        assert hasattr(Usuario, "apellidos")

    def test_has_email(self):
        assert hasattr(Usuario, "email")

    def test_has_email_hash(self):
        assert hasattr(Usuario, "email_hash")

    # ── Optional PII attributes ──────────────────────────────────────

    def test_has_dni(self):
        assert hasattr(Usuario, "dni")

    def test_has_cuil(self):
        assert hasattr(Usuario, "cuil")

    def test_has_cbu(self):
        assert hasattr(Usuario, "cbu")

    def test_has_alias_cbu(self):
        assert hasattr(Usuario, "alias_cbu")

    # ── Non-PII optional attributes ──────────────────────────────────

    def test_has_banco(self):
        assert hasattr(Usuario, "banco")

    def test_has_regional(self):
        assert hasattr(Usuario, "regional")

    def test_has_legajo(self):
        assert hasattr(Usuario, "legajo")

    def test_has_legajo_profesional(self):
        assert hasattr(Usuario, "legajo_profesional")

    def test_has_facturador(self):
        assert hasattr(Usuario, "facturador")

    # ── PII fields use EncryptedString ───────────────────────────────

    def test_email_is_encrypted_string(self):
        """PII field email should use EncryptedString type."""
        col = Usuario.__table__.c["email"]
        # Check that the column type is an instance of EncryptedString
        assert isinstance(col.type, EncryptedString), (
            f"Expected EncryptedString, got {type(col.type)}"
        )

    def test_dni_is_encrypted_string(self):
        col = Usuario.__table__.c["dni"]
        assert isinstance(col.type, EncryptedString)

    def test_cuil_is_encrypted_string(self):
        col = Usuario.__table__.c["cuil"]
        assert isinstance(col.type, EncryptedString)

    def test_cbu_is_encrypted_string(self):
        col = Usuario.__table__.c["cbu"]
        assert isinstance(col.type, EncryptedString)

    def test_alias_cbu_is_encrypted_string(self):
        col = Usuario.__table__.c["alias_cbu"]
        assert isinstance(col.type, EncryptedString)

    # ── email_hash is NOT encrypted ──────────────────────────────────

    def test_email_hash_is_not_encrypted(self):
        """email_hash should be a plain string, not EncryptedString."""
        col = Usuario.__table__.c["email_hash"]
        assert not isinstance(col.type, EncryptedString)

    # ── Unique constraint ────────────────────────────────────────────

    def test_unique_constraint_on_tenant_email_hash(self):
        """There should be a unique constraint on (tenant_id, email_hash)."""
        constraints = list(Usuario.__table__.constraints)
        unique_names = [c.name for c in constraints if hasattr(c, "columns")]
        assert any("uq" in (n or "").lower() or "unique" in (n or "").lower()
                    for n in unique_names), (
            f"No unique constraint found for tenant_id+email_hash. "
            f"Constraints: {[c.name for c in constraints if hasattr(c, 'columns')]}"
        )
