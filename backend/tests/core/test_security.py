"""Tests for core.security — AES-256-GCM encryption and decryption."""

import re

import pytest
from app.core.security import aes_decrypt, aes_encrypt, get_encryption_key

# Valid 32-byte key for tests
VALID_KEY = b"a" * 32
OTHER_KEY = b"b" * 32


class TestAESEncryptDecrypt:
    """AES-256-GCM roundtrip, uniqueness, and error handling."""

    # ── Scenario: Encrypt and decrypt roundtrip ──────────────────────

    def test_roundtrip_returns_original_text(self):
        """Encrypting then decrypting should return the original plaintext."""
        plaintext = "sensitive-data"
        encrypted = aes_encrypt(plaintext, VALID_KEY)
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        decrypted = aes_decrypt(encrypted, VALID_KEY)
        assert decrypted == plaintext

    def test_roundtrip_with_unicode(self):
        """Encrypt/decrypt should handle unicode characters."""
        plaintext = "áéíóúñÑü¡¿🔥"
        encrypted = aes_encrypt(plaintext, VALID_KEY)
        decrypted = aes_decrypt(encrypted, VALID_KEY)
        assert decrypted == plaintext

    # ── Scenario: Different ciphertext per encryption ────────────────

    def test_different_ciphertext_per_call(self):
        """Each encryption should produce different output (random nonce)."""
        plaintext = "same-data"
        result1 = aes_encrypt(plaintext, VALID_KEY)
        result2 = aes_encrypt(plaintext, VALID_KEY)
        assert result1 != result2

    def test_base64_url_safe_no_padding(self):
        """Output should be URL-safe base64 without padding issues."""
        plaintext = "data"
        encrypted = aes_encrypt(plaintext, VALID_KEY)
        # URL-safe base64: letters, digits, -, _, and =
        assert re.match(r"^[A-Za-z0-9\-_=]+$", encrypted), (
            f"Output contains invalid base64 chars: {encrypted}"
        )

    # ── Scenario: Decrypt with wrong key fails ───────────────────────

    def test_wrong_key_raises_error(self):
        """Decrypting with a different key should fail."""
        plaintext = "secret-info"
        encrypted = aes_encrypt(plaintext, VALID_KEY)
        with pytest.raises(Exception):
            aes_decrypt(encrypted, OTHER_KEY)

    # ── Scenario: Invalid key length raises ValueError ───────────────

    def test_encrypt_short_key_raises_value_error(self):
        """Encrypting with a non-32-byte key should raise ValueError."""
        with pytest.raises(ValueError, match="32 bytes"):
            aes_encrypt("data", b"short")

    def test_encrypt_empty_key_raises_value_error(self):
        """Encrypting with an empty key should raise ValueError."""
        with pytest.raises(ValueError, match="32 bytes"):
            aes_encrypt("data", b"")

    def test_decrypt_short_key_raises_value_error(self):
        """Decrypting with a non-32-byte key should raise ValueError."""
        encrypted = aes_encrypt("data", VALID_KEY)
        with pytest.raises(ValueError, match="32 bytes"):
            aes_decrypt(encrypted, b"short")

    # ── Scenario: Encrypt with empty string ──────────────────────────

    def test_encrypt_empty_string(self):
        """Encrypting an empty string should work and roundtrip."""
        encrypted = aes_encrypt("", VALID_KEY)
        decrypted = aes_decrypt(encrypted, VALID_KEY)
        assert decrypted == ""

    # ── Scenario: get_encryption_key returns bytes ───────────────────

    def test_get_encryption_key_returns_bytes(self):
        """get_encryption_key() should return a bytes object."""
        key = get_encryption_key()
        assert isinstance(key, bytes)

    def test_get_encryption_key_is_32_bytes(self):
        """get_encryption_key() should return a 32-byte key from ENCRYPTION_KEY setting."""
        key = get_encryption_key()
        assert len(key) == 32
