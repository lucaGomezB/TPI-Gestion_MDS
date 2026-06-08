"""SyncLog model — tracks every sync execution for traceability.

Each sync (nocturnal, on-demand, manual import) creates a SyncLog entry
with status, timing, step-level details, and error information.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel


class SyncLog(AppModel):
    """Record of a single sync execution.

    Attributes:
        tenant_id: The tenant that owns this sync.
        dictado_id: Optional dictado for per-dictado syncs.
        sync_type: 'nocturnal', 'ondemand', or 'manual_import'.
        status: 'running', 'completed', 'failed', or 'partial'.
        started_at: When the sync started.
        finished_at: When the sync finished (nullable for running).
        details: JSONB with step-level details.
        error_message: Top-level error message (nullable).
    """

    __tablename__ = "sync_log"

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dictado_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        index=True,
    )
    sync_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="running",
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    details: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
