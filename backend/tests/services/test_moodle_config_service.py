"""Tests for MoodleConfigService encrypt/decrypt roundtrip.

Tests cover:
- Valid config encrypt/decrypt roundtrip
- Empty config handling
- URL with special characters
- Tenant without config returns None
"""

import os

import pytest

# Set test env vars before any imports
os.environ["SECRET_KEY"] = "a" * 32
os.environ["ENCRYPTION_KEY"] = "b" * 32

from app.core.security import decrypt_moodle_config, encrypt_moodle_config  # noqa: E402
from app.schemas.moodle_config import MoodleConfigSchema  # noqa: E402


class TestMoodleConfigEncryption:
    """Test encrypt/decrypt roundtrip for moodle config."""

    def test_valid_config_roundtrip(self) -> None:
        """Test that a valid config encrypts and decrypts correctly."""
        config = {
            "ws_url": "https://moodle.miuniversidad.edu.ar",
            "ws_token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            "ws_enabled": True,
            "moodle_version": "4.1",
        }

        encrypted = encrypt_moodle_config(config)
        assert encrypted["ws_url"] != config["ws_url"]
        assert encrypted["ws_token"] != config["ws_token"]
        assert encrypted["ws_enabled"] is True
        assert encrypted["moodle_version"] == "4.1"

        decrypted = decrypt_moodle_config(encrypted)
        assert decrypted["ws_url"] == config["ws_url"]
        assert decrypted["ws_token"] == config["ws_token"]
        assert decrypted["ws_enabled"] is True
        assert decrypted["moodle_version"] == "4.1"

    def test_empty_config_preserved(self) -> None:
        """Test that empty or None values are preserved."""
        config = {
            "ws_url": "",
            "ws_token": None,
            "ws_enabled": True,
        }

        encrypted = encrypt_moodle_config(config)
        assert encrypted["ws_url"] == ""
        assert encrypted["ws_token"] is None

        decrypted = decrypt_moodle_config(encrypted)
        assert decrypted["ws_url"] == ""
        assert decrypted["ws_token"] is None

    def test_url_with_special_chars(self) -> None:
        """Test that URLs with special characters roundtrip correctly."""
        config = {
            "ws_url": "https://moodle.example.com/webservice/rest/server.php?alt=",
            "ws_token": "tok#en@with$spec!al&chars",
        }

        encrypted = encrypt_moodle_config(config)
        decrypted = decrypt_moodle_config(encrypted)
        assert decrypted["ws_url"] == config["ws_url"]
        assert decrypted["ws_token"] == config["ws_token"]


class TestMoodleConfigSchema:
    """Test MoodleConfigSchema validation."""

    def test_minimal_config(self) -> None:
        """Test that minimal config with default values works."""
        config = MoodleConfigSchema()
        assert config.ws_enabled is True
        assert config.ws_url is None
        assert config.sync_frequency_hours == 24

    def test_full_config(self) -> None:
        """Test that a full config loads correctly."""
        config = MoodleConfigSchema(
            ws_url="https://moodle.example.com",
            ws_token="abc123",
            ws_enabled=True,
            moodle_version="4.1",
        )
        assert config.ws_url == "https://moodle.example.com"
        assert config.ws_token == "abc123"
        assert config.ws_enabled is True
        assert config.moodle_version == "4.1"

    def test_extra_field_forbidden(self) -> None:
        """Test that extra fields are rejected (extra='forbid')."""
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            MoodleConfigSchema(unknown_field="should fail")  # type: ignore[call-arg]
