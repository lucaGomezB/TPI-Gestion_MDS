"""Tests for EncryptedString TypeDecorator — transparent AES encryption at the ORM level."""

from unittest.mock import patch

import pytest
from app.models.types import EncryptedString
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator


class TestEncryptedStringType:
    """EncryptedString TypeDecorator wraps aes_encrypt/aes_decrypt."""

    def test_is_type_decorator(self):
        """EncryptedString should subclass TypeDecorator."""
        assert issubclass(EncryptedString, TypeDecorator)

    def test_impl_is_text(self):
        """The underlying storage type should be Text (not String with length)."""
        type_ = EncryptedString()
        assert isinstance(type_.impl, Text)

    # ── Scenario: process_bind_param encrypts on write ───────────────

    def test_bind_param_encrypts_plaintext(self):
        """process_bind_param should return an encrypted base64 string."""
        type_ = EncryptedString()
        result = type_.process_bind_param("hello", None)
        assert result is not None
        assert isinstance(result, str)
        # Result should look like base64
        assert len(result) > len("hello")  # encrypted output is larger

    def test_bind_param_different_each_call(self):
        """Each call to process_bind_param should produce different output."""
        type_ = EncryptedString()
        r1 = type_.process_bind_param("hello", None)
        r2 = type_.process_bind_param("hello", None)
        assert r1 != r2

    # ── Scenario: process_result_value decrypts on read ──────────────

    def test_result_value_decrypts_ciphertext(self):
        """process_result_value should return original plaintext from encrypted."""
        type_ = EncryptedString()
        encrypted = type_.process_bind_param("secret-data", None)
        decrypted = type_.process_result_value(encrypted, None)
        assert decrypted == "secret-data"

    # ── Scenario: Full roundtrip ─────────────────────────────────────

    def test_bind_result_roundtrip(self):
        """Going bind → result should return the original value."""
        type_ = EncryptedString()
        original = "test@example.com"
        bound = type_.process_bind_param(original, None)
        result = type_.process_result_value(bound, None)
        assert result == original

    # ── Scenario: None passes through ────────────────────────────────

    def test_bind_param_none_returns_none(self):
        """process_bind_param should pass None through without encrypting."""
        type_ = EncryptedString()
        assert type_.process_bind_param(None, None) is None

    def test_result_value_none_returns_none(self):
        """process_result_value should pass None through without decrypting."""
        type_ = EncryptedString()
        assert type_.process_result_value(None, None) is None

    def test_result_value_empty_string(self):
        """process_result_value should handle any non-None string (decrypts it)."""
        type_ = EncryptedString()
        encrypted = type_.process_bind_param("", None)
        decrypted = type_.process_result_value(encrypted, None)
        assert decrypted == ""
