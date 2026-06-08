"""Repository for SyncLog CRUD operations.

Provides methods to create, update, and query sync log entries
with automatic tenant scoping.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sync_log import SyncLog


class SyncLogRepository:
    """Repository for managing SyncLog entries."""

    def __init__(self, session: AsyncSession, tenant_id: str | None = None) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def create(
        self,
        sync_type: str,
        status: str = "running",
        dictado_id: str | None = None,
        details: dict | None = None,
    ) -> SyncLog:
        """Create a new sync log entry.

        Args:
            sync_type: 'nocturnal', 'ondemand', or 'manual_import'.
            status: Initial status (default 'running').
            dictado_id: Optional dictado UUID.
            details: Optional JSONB details dict.

        Returns:
            The created SyncLog instance.
        """
        log = SyncLog(
            tenant_id=self.tenant_id,
            dictado_id=dictado_id,
            sync_type=sync_type,
            status=status,
            details=details or {},
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def update_status(
        self,
        log_id: str,
        status: str,
        error_message: str | None = None,
        details: dict | None = None,
    ) -> SyncLog | None:
        """Update the status of a sync log entry.

        Args:
            log_id: The SyncLog UUID.
            status: New status value.
            error_message: Optional error message.
            details: Optional updated details dict.

        Returns:
            The updated SyncLog or None if not found.
        """
        result = await self.session.execute(
            select(SyncLog).where(
                SyncLog.id == log_id,
                SyncLog.tenant_id == self.tenant_id,
            )
        )
        log = result.scalar_one_or_none()
        if log is None:
            return None

        log.status = status
        log.finished_at = datetime.now(timezone.utc)

        if error_message is not None:
            log.error_message = error_message
        if details is not None:
            log.details = details

        await self.session.flush()
        return log

    async def list_by_dictado(
        self, dictado_id: str, limit: int = 20
    ) -> list[SyncLog]:
        """List sync log entries for a specific dictado, newest first.

        Args:
            dictado_id: The dictado UUID.
            limit: Maximum number of entries (default 20).

        Returns:
            A list of SyncLog entries.
        """
        result = await self.session.execute(
            select(SyncLog)
            .where(
                SyncLog.tenant_id == self.tenant_id,
                SyncLog.dictado_id == dictado_id,
            )
            .order_by(desc(SyncLog.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_tenant(
        self, limit: int = 50, sync_type: str | None = None
    ) -> list[SyncLog]:
        """List sync log entries for the current tenant.

        Args:
            limit: Maximum number of entries (default 50).
            sync_type: Optional filter by sync type.

        Returns:
            A list of SyncLog entries.
        """
        stmt = (
            select(SyncLog)
            .where(SyncLog.tenant_id == self.tenant_id)
            .order_by(desc(SyncLog.created_at))
            .limit(limit)
        )
        if sync_type:
            stmt = stmt.where(SyncLog.sync_type == sync_type)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def has_running_sync(self, dictado_id: str) -> bool:
        """Check if a sync is already running for a dictado.

        Args:
            dictado_id: The dictado UUID.

        Returns:
            ``True`` if a sync with status 'running' exists.
        """
        result = await self.session.execute(
            select(SyncLog)
            .where(
                SyncLog.tenant_id == self.tenant_id,
                SyncLog.dictado_id == dictado_id,
                SyncLog.status == "running",
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
