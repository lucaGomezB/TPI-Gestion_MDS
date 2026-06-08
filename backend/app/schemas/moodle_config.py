"""Pydantic schemas for per-tenant Moodle configuration.

All schemas use ``extra='forbid'`` to reject undeclared fields.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MoodleConfigSchema(BaseModel):
    """Per-tenant Moodle Web Services configuration.

    Sensitive fields (ws_url, ws_token) are encrypted at rest.
    """

    model_config = ConfigDict(extra="forbid")

    ws_url: str | None = None
    ws_token: str | None = None
    ws_enabled: bool = True
    moodle_version: str | None = None
    last_sync_at: datetime | None = None
    sync_frequency_hours: int = 24


class MoodleConfigUpdateSchema(BaseModel):
    """Schema for updating Moodle configuration.

    Only the fields that are provided will be updated.
    """

    model_config = ConfigDict(extra="forbid")

    ws_url: str | None = None
    ws_token: str | None = None
    ws_enabled: bool | None = None
    moodle_version: str | None = None
    sync_frequency_hours: int | None = None
