"""Repositories for Comunicacion and LoteComunicacion.

Provides tenant-scoped queries for the communications queue system:
- ``ComunicacionRepository``: Individual communication CRUD + batch operations
- ``LoteRepository``: Batch-level CRUD + worker queue queries

Both inherit from ``BaseRepository`` and scope all queries by ``tenant_id``.
"""

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunicacion import (
    Comunicacion,
    EstadoComunicacion,
    EstadoLote,
    LoteComunicacion,
)
from app.repositories.base import BaseRepository


class ComunicacionRepository(BaseRepository[Comunicacion]):
    """Tenant-scoped CRUD for individual communications with batch operations.

    Worker-specific queries:
    - ``find_pendientes_for_worker`` — items ready for processing
    - ``bulk_create`` — batch insert for bulk sends
    - ``bulk_update_status`` — batch status transitions
    - ``cancel_by_lote`` — cancel all pending items in a batch
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = Comunicacion

    # ── Finder queries ─────────────────────────────────────────────────

    async def find_by_lote(self, lote_id: str) -> list[Comunicacion]:
        """Get all communications for a specific lote."""
        model = self.model_class
        stmt = self._stmt().where(model.lote_id == lote_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_materia(self, materia_id: str) -> list[Comunicacion]:
        """Get all communications for a materia."""
        model = self.model_class
        stmt = self._stmt().where(model.materia_id == materia_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_pendientes_for_worker(
        self,
        batch_size: int = 50,
    ) -> list[Comunicacion]:
        """Find communications ready for worker processing.

        Selects Pendiente communications that belong to a lote that is
        either Enviando or Pendiente (queued but not requiring approval).
        Communications with retry_count >= 3 are excluded (permanent failures).

        Args:
            batch_size: Maximum number of items to fetch.

        Returns:
            List of Comunicacion instances ready for processing.
        """
        model = self.model_class
        stmt = (
            select(model)
            .join(LoteComunicacion, model.lote_id == LoteComunicacion.id)
            .where(
                model.estado == EstadoComunicacion.pendiente.value,
                LoteComunicacion.estado.in_([
                    EstadoLote.enviando.value,
                    EstadoLote.pendiente.value,
                ]),
                model.retry_count < 3,
            )
            .limit(batch_size)
        )
        # Apply tenant scoping
        if self.tenant_id is not None:
            stmt = stmt.where(model.tenant_id == self.tenant_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Batch operations ───────────────────────────────────────────────

    async def bulk_create(self, entries: list[dict[str, Any]]) -> list[Comunicacion]:
        """Create multiple communications in a single transaction.

        Args:
            entries: List of dicts with Comunicacion field values.

        Returns:
            List of created Comunicacion instances (flushed, not committed).
        """
        instances = []
        for data in entries:
            if self.tenant_id is not None and "tenant_id" not in data:
                data["tenant_id"] = self.tenant_id
            instance = Comunicacion(**data)
            self.session.add(instance)
            instances.append(instance)
        await self.session.flush()
        return instances

    async def bulk_update_status(
        self,
        ids: list[str],
        estado: str,
        error_msg: str | None = None,
    ) -> None:
        """Batch update status for multiple communications.

        Args:
            ids: List of communication UUIDs to update.
            estado: Target state (e.g. ``Enviado``, ``Error``).
            error_msg: Optional error message (cleared if None).
        """
        model = self.model_class
        values: dict[str, Any] = {"estado": estado}
        if error_msg is not None:
            values["error_msg"] = error_msg

        stmt = (
            update(model)
            .where(model.id.in_(ids))
            .values(**values)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def cancel_by_lote(self, lote_id: str) -> int:
        """Cancel all Pendiente communications for a given lote.

        Args:
            lote_id: The lote UUID.

        Returns:
            Number of cancelled communications.
        """
        model = self.model_class
        stmt = (
            update(model)
            .where(
                model.lote_id == lote_id,
                model.estado == EstadoComunicacion.pendiente.value,
            )
            .values(estado=EstadoComunicacion.cancelado.value)
            .returning(model.id)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return len(result.all())


class LoteRepository(BaseRepository[LoteComunicacion]):
    """Tenant-scoped CRUD for communication batches.

    Worker-specific queries:
    - ``find_ready_for_worker`` — lotes ready for processing
    - ``update_counters`` — aggregate counters after processing
    - ``find_pending_approval`` — lotes awaiting admin decision
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = LoteComunicacion

    # ── Finder queries ─────────────────────────────────────────────────

    async def find_ready_for_worker(self) -> list[LoteComunicacion]:
        """Find lotes ready for worker processing.

        Returns lotes with estado=Pendiente that do NOT require approval
        (or have already been approved and are in Enviando state).

        Returns:
            List of LoteComunicacion instances ready for processing.
        """
        model = self.model_class
        stmt = self._stmt().where(
            model.estado.in_([
                EstadoLote.pendiente.value,
                EstadoLote.enviando.value,
            ]),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_materia(self, materia_id: str) -> list[LoteComunicacion]:
        """List all lotes for a materia (for status tracking)."""
        model = self.model_class
        stmt = self._stmt().where(model.materia_id == materia_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_counters(
        self,
        lote_id: str,
        enviados: int,
        fallidos: int,
    ) -> LoteComunicacion | None:
        """Update the aggregated counters for a lote.

        Also computes the final estado based on counters:
        - If all sent: Completado
        - If all failed: Cancelado
        - If mixed: Parcial

        Args:
            lote_id: The lote UUID.
            enviados: Number of successfully sent communications.
            fallidos: Number of failed communications.

        Returns:
            The updated LoteComunicacion, or None if not found.
        """
        model = self.model_class

        # Determine final estado
        total = enviados + fallidos
        if total == 0:
            final_estado = EstadoLote.pendiente.value
        elif fallidos == 0:
            final_estado = EstadoLote.completado.value
        elif enviados == 0:
            final_estado = EstadoLote.cancelado.value
        else:
            final_estado = EstadoLote.parcial.value

        stmt = (
            update(model)
            .where(model.id == lote_id)
            .values(
                enviados=enviados,
                fallidos=fallidos,
                estado=final_estado,
            )
            .returning(model)
        )
        if self.tenant_id is not None:
            stmt = stmt.where(model.tenant_id == self.tenant_id)

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def find_pending_approval(self) -> list[LoteComunicacion]:
        """Find lotes awaiting approval (estado = AprobacionPendiente).

        Returns:
            List of LoteComunicacion instances requiring approval.
        """
        model = self.model_class
        stmt = self._stmt().where(
            model.estado == EstadoLote.aprobacion_pendiente.value,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
