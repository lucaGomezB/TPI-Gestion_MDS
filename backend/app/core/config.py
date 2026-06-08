"""Application configuration via pydantic-settings."""

from typing import ClassVar

from pydantic import Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-level settings loaded from environment variables or .env file.

    All secrets (SECRET_KEY, ENCRYPTION_KEY) must be at least 32 characters long.
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://activia:activia@localhost:5432/activia_trace",
        alias="DATABASE_URL",
    )

    # --- Auth / Security ---
    secret_key: str = Field(default=..., min_length=32, alias="SECRET_KEY")
    encryption_key: str = Field(default=..., min_length=32, alias="ENCRYPTION_KEY")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    totp_issuer_name: str = Field(default="activia-trace", alias="TOTP_ISSUER_NAME")

    # --- Environment ---
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="DEBUG", alias="LOG_LEVEL")

    # --- Moodle Integration ---
    moodle_sync_hour: int = Field(default=3, alias="MOODLE_SYNC_HOUR")
    moodle_request_timeout: int = Field(default=30, alias="MOODLE_REQUEST_TIMEOUT")

    # --- SMTP / Email ---
    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    smtp_from_email: str = Field(default="noreply@activia-trace.com", alias="SMTP_FROM_EMAIL")
    smtp_from_name: str = Field(default="activia-trace", alias="SMTP_FROM_NAME")

    # --- Uploads ---
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")

    # --- Worker ---
    worker_poll_interval: int = Field(default=30, alias="WORKER_POLL_INTERVAL")
    worker_max_retries: int = Field(default=3, alias="WORKER_MAX_RETRIES")

    @model_validator(mode="after")
    def _production_defaults(self) -> "Settings":
        """Apply production-safe defaults when environment is 'production'."""
        if self.environment == "production":
            self.debug = False
        return self

    @model_validator(mode="after")
    def _validate_encryption_key_length(self) -> "Settings":
        """Validate that encryption_key is at least 32 characters."""
        key = self.encryption_key
        if len(key) < 32:
            raise ValueError(
                f"ENCRYPTION_KEY must be at least 32 characters (got {len(key)})."
            )
        return self


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the singleton Settings instance, loading it on first call."""
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
