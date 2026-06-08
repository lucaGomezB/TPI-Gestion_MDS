"""Tests for core.config — Settings via pydantic-settings."""

import pytest
from app.core.config import Settings

_DEV_SECRET = "a" * 32
_DEV_ENCRYPTION = "b" * 32


class TestSettingsDefaults:
    """Settings should load reasonable defaults when .env is absent."""

    def test_default_database_url(self):
        """Default DATABASE_URL matches the dev expectation."""
        settings = Settings(
            SECRET_KEY=_DEV_SECRET,
            ENCRYPTION_KEY=_DEV_ENCRYPTION,
            _env_file=None,  # type: ignore[call-arg]
        )
        assert str(settings.database_url) == "postgresql+asyncpg://activia:activia@localhost:5432/activia_trace"

    def test_default_secret_key_raises_on_short(self):
        """Secret key shorter than 32 chars should raise."""
        with pytest.raises(ValueError, match="SECRET_KEY"):
            Settings(SECRET_KEY="short", ENCRYPTION_KEY=_DEV_ENCRYPTION, _env_file=None)  # type: ignore[call-arg]

    def test_default_encryption_key_raises_on_short(self):
        """Encryption key shorter than 32 chars should raise."""
        with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
            Settings(SECRET_KEY=_DEV_SECRET, ENCRYPTION_KEY="short", _env_file=None)  # type: ignore[call-arg]

    def test_default_access_token_expire_minutes(self):
        """ACCESS_TOKEN_EXPIRE_MINUTES defaults to 15."""
        settings = Settings(
            SECRET_KEY=_DEV_SECRET,
            ENCRYPTION_KEY=_DEV_ENCRYPTION,
            _env_file=None,  # type: ignore[call-arg]
        )
        assert settings.access_token_expire_minutes == 15

    def test_default_environment(self):
        """ENVIRONMENT defaults to 'development'."""
        settings = Settings(
            SECRET_KEY=_DEV_SECRET,
            ENCRYPTION_KEY=_DEV_ENCRYPTION,
            _env_file=None,  # type: ignore[call-arg]
        )
        assert settings.environment == "development"

    def test_default_debug(self):
        """DEBUG defaults to True."""
        settings = Settings(
            SECRET_KEY=_DEV_SECRET,
            ENCRYPTION_KEY=_DEV_ENCRYPTION,
            _env_file=None,  # type: ignore[call-arg]
        )
        assert settings.debug is True

    def test_default_log_level(self):
        """LOG_LEVEL defaults to 'DEBUG'."""
        settings = Settings(
            SECRET_KEY=_DEV_SECRET,
            ENCRYPTION_KEY=_DEV_ENCRYPTION,
            _env_file=None,  # type: ignore[call-arg]
        )
        assert settings.log_level == "DEBUG"


class TestSettingsEnvOverride:
    """Settings should respect environment variable overrides."""

    _dev_kwargs: dict = {
        "SECRET_KEY": _DEV_SECRET,
        "ENCRYPTION_KEY": _DEV_ENCRYPTION,
        "_env_file": None,  # type: ignore[arg-type]
    }

    def test_env_variable_override(self, monkeypatch):
        """Setting DATABASE_URL via env var overrides the default."""
        test_url = "postgresql+asyncpg://test:test@localhost:9999/test_db"
        monkeypatch.setenv("DATABASE_URL", test_url)
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        settings = Settings(_env_file=None)  # type: ignore[call-arg]
        assert str(settings.database_url) == test_url

    def test_environment_override(self, monkeypatch):
        """Setting ENVIRONMENT via env var overrides the default."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        settings = Settings(**self._dev_kwargs)
        assert settings.environment == "production"
        assert settings.debug is False

    def test_debug_true_when_development(self, monkeypatch):
        """DEBUG should be True when ENVIRONMENT is development."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        settings = Settings(**self._dev_kwargs)
        assert settings.debug is True

    def test_debug_false_when_production(self, monkeypatch):
        """DEBUG should be False when ENVIRONMENT is production."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        settings = Settings(**self._dev_kwargs)
        assert settings.debug is False
