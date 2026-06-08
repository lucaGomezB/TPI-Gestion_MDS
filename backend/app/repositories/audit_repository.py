"""Audit repository — append-only, create/search interface for ``AuditLog``.

This repository deliberately exposes only:
- ``create()`` — insert a new audit entry
- ``search()`` — full-text search with filters, paginated
- ``count()`` — count results matching filters
- ``get_docente_interacciones()`` — aggregated metrics per teacher
- ``export_search()`` — unfiltered export data (no pagination limit)

It does NOT expose ``update()`` or ``delete()`` methods. Append-only is
enforced at three layers (repository, ORM event listener, DB trigger).
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.audit_log import AuditLog


class AuditRepository:
    """Append-only repository for audit log entries.

    Args:
        session: An active SQLAlchemy ``AsyncSession``.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Create (append-only) ────────────────────────────────────────────────

    async def create(self, data: dict) -> AuditLog:
        """Persist a new audit log entry.

        Args:
            data: Dictionary of attributes for the ``AuditLog`` instance.

        Returns:
            The created ``AuditLog`` instance (after flush, not committed).
        """
        entry = AuditLog(**data)
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    # ── Search with full-text + filters ─────────────────────────────────────

    async def search(
        self,
        tenant_id: str,
        q: str | None = None,
        accion: str | None = None,
        actor_id: str | None = None,
        materia_id: str | None = None,
        ip: str | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """Full-text search with optional filters.

        All queries are scoped to ``tenant_id`` first, then filters are
        applied conjunctively.

        Args:
            tenant_id: Required — scopes all results to this tenant.
            q: Full-text search query (uses ``plainto_tsquery('spanish', ...)``).
            accion: Exact match on action code.
            actor_id: Exact match on actor UUID.
            materia_id: Exact match on materia UUID.
            ip: Exact match on IP address.
            fecha_desde: Lower bound for ``fecha_hora`` (inclusive).
            fecha_hasta: Upper bound for ``fecha_hora`` (inclusive).
            limit: Page size (default 50, max 200).
            offset: Pagination offset (default 0).

        Returns:
            A tuple of ``(items: list[AuditLog], total: int)``.
        """
        base_query = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
        count_query = select(func.count(AuditLog.id)).where(
            AuditLog.tenant_id == tenant_id
        )

        # Full-text search
        if q:
            ts_query = func.plainto_tsquery("spanish", q)
            filter_cond = AuditLog.search_vector.op("@@")(ts_query)  # type: ignore[attr-defined]
            base_query = base_query.where(filter_cond)
            count_query = count_query.where(filter_cond)

        # Exact filters
        if accion:
            base_query = base_query.where(AuditLog.accion == accion)
            count_query = count_query.where(AuditLog.accion == accion)
        if actor_id:
            base_query = base_query.where(AuditLog.actor_id == actor_id)
            count_query = count_query.where(AuditLog.actor_id == actor_id)
        if materia_id:
            base_query = base_query.where(AuditLog.materia_id == materia_id)
            count_query = count_query.where(AuditLog.materia_id == materia_id)
        if ip:
            base_query = base_query.where(AuditLog.ip == ip)
            count_query = count_query.where(AuditLog.ip == ip)
        if fecha_desde:
            base_query = base_query.where(AuditLog.fecha_hora >= fecha_desde)
            count_query = count_query.where(AuditLog.fecha_hora >= fecha_desde)
        if fecha_hasta:
            base_query = base_query.where(AuditLog.fecha_hora <= fecha_hasta)
            count_query = count_query.where(AuditLog.fecha_hora <= fecha_hasta)

        # Order by fecha_hora DESC (most recent first)
        base_query = base_query.order_by(AuditLog.fecha_hora.desc())

        # Pagination
        base_query = base_query.limit(min(limit, 200)).offset(offset)

        # Execute
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        items_result = await self.session.execute(base_query)
        items = list(items_result.scalars().all())

        return items, total

    # ── Docente interacciones (aggregated metrics, F9.1) ────────────────────

    async def get_docente_interacciones(
        self, tenant_id: str, docente_id: str
    ) -> dict[str, Any]:
        """Get aggregated interaction metrics for a teacher (F9.1).

        Args:
            tenant_id: Required — scopes results to the caller's tenant.
            docente_id: The teacher's UUID.

        Returns:
            A dict with:
            - ``total_acciones``: total count of actions.
            - ``por_accion``: dict mapping action code → count.
            - ``por_materia``: list of ``{materia_id, total}`` dicts.
            - ``ultimas_acciones``: list of most recent 200 ``AuditLog`` entries.
        """
        # Total count
        total_result = await self.session.execute(
            select(func.count(AuditLog.id)).where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.actor_id == docente_id,
            )
        )
        total_acciones: int = total_result.scalar_one()

        # Count by action
        by_action_result = await self.session.execute(
            select(AuditLog.accion, func.count(AuditLog.id).label("cnt"))
            .where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.actor_id == docente_id,
            )
            .group_by(AuditLog.accion)
        )
        por_accion: dict[str, int] = {}
        for row in by_action_result:
            por_accion[row.accion] = row.cnt

        # Count by materia
        by_materia_result = await self.session.execute(
            select(AuditLog.materia_id, func.count(AuditLog.id).label("cnt"))
            .where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.actor_id == docente_id,
                AuditLog.materia_id.isnot(None),
            )
            .group_by(AuditLog.materia_id)
            .order_by(text("cnt DESC"))
        )
        por_materia = [
            {"materia_id": row.materia_id, "total": row.cnt}
            for row in by_materia_result
        ]

        # Last 200 actions
        ultimas_result = await self.session.execute(
            select(AuditLog)
            .where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.actor_id == docente_id,
            )
            .order_by(AuditLog.fecha_hora.desc())
            .limit(200)
        )
        ultimas_acciones = list(ultimas_result.scalars().all())

        return {
            "docente_id": docente_id,
            "total_acciones": total_acciones,
            "por_accion": por_accion,
            "por_materia": por_materia,
            "ultimas_acciones": ultimas_acciones,
        }

    # ── Export (unpaginated results for export) ─────────────────────────────

    async def export_search(
        self,
        tenant_id: str,
        q: str | None = None,
        accion: str | None = None,
        actor_id: str | None = None,
        materia_id: str | None = None,
        ip: str | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Return raw audit data for export (no pagination limit).

        Accepts the same filters as ``search()`` but returns ALL matching
        results (suitable for CSV/JSON export).

        Args:
            Same filter parameters as ``search()`` (without limit/offset).

        Returns:
            A list of dicts, each representing an ``AuditLog`` entry.
        """
        items, _ = await self.search(
            tenant_id=tenant_id,
            q=q,
            accion=accion,
            actor_id=actor_id,
            materia_id=materia_id,
            ip=ip,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limit=999999,  # effectively unlimited for export
            offset=0,
        )
        return [
            {
                "id": e.id,
                "tenant_id": e.tenant_id,
                "fecha_hora": e.fecha_hora.isoformat()
                if e.fecha_hora
                else None,
                "actor_id": e.actor_id,
                "impersonado_id": e.impersonado_id,
                "materia_id": e.materia_id,
                "accion": e.accion,
                "detalle": e.detalle,
                "filas_afectadas": e.filas_afectadas,
                "ip": e.ip,
                "user_agent": e.user_agent,
            }
            for e in items
        ]
