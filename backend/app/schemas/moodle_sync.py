"""Pydantic schemas for Moodle sync engine operations.

All schemas use ``extra='forbid'`` to reject undeclared fields.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SyncStep(BaseModel):
    """Represents a single step in the sync pipeline.

    Each step (fetch activities, fetch users, fetch grades, persist, etc.)
    has its own status and error handling.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    status: str = "pending"  # pending, running, completed, failed, skipped
    records_affected: int = 0
    error: str | None = None


class SyncResult(BaseModel):
    """Result of a sync operation returned to the caller."""

    model_config = ConfigDict(extra="forbid")

    status: str  # completed, partial, failed
    sync_log_id: str | None = None
    activities_synced: int = 0
    students_synced: int = 0
    grade_items_synced: int = 0
    errors: list[str] = []


class SyncRequest(BaseModel):
    """Request body for triggering an on-demand sync.

    Currently empty — sync is triggered for the dictado specified in the URL.
    Reserved for future query parameters (e.g., ``force_full_sync``).
    """

    model_config = ConfigDict(extra="forbid")
