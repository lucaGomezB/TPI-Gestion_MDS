"""MensajeRepository — tenant-scoped CRUD for internal messaging (C-13).

Provides queries for inbox listing, thread management, unread counting,
and per-user soft-delete tracking.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select, and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.hilo_mensaje import HiloMensaje
from app.models.mensaje import Mensaje
from app.models.mensaje_eliminado import MensajeEliminado
from app.models.usuario import Usuario
from app.repositories.base import BaseRepository


class MensajeRepository(BaseRepository[Mensaje]):
    """Tenant-scoped CRUD for internal messaging.

    Specialized queries for:
    - ``list_inbox``: Paginated thread summaries for a user
    - ``get_thread``: All messages in a thread, filtered by deletions
    - ``get_or_create_hilo``: Thread dedup by participants + asunto
    - ``mark_as_read``: Batch update leido for messages addressed to user
    - ``count_no_leidos``: Unread message count for a user
    - ``soft_delete_for_user``: Per-user message deletion
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = Mensaje

    # ── Thread management ──────────────────────────────────────────────

    async def find_or_create_hilo(
        self,
        tenant_id: str,
        participantes: list[str],
        asunto: str,
    ) -> HiloMensaje:
        """Find an existing thread or create a new one.

        A thread is considered matching if it has the same ``asunto``
        between the same participants (order-independent).

        Args:
            tenant_id: Tenant UUID.
            participantes: List of participant user UUIDs (sorted).
            asunto: Thread subject.

        Returns:
            The existing or newly created HiloMensaje.
        """
        # Sort participants for order-independent comparison
        sorted_participantes = sorted(participantes)

        # Look for existing thread with same asunto and participants
        stmt = (
            select(HiloMensaje)
            .where(
                HiloMensaje.tenant_id == tenant_id,
                HiloMensaje.asunto == asunto,
            )
        )
        result = await self.session.execute(stmt)
        existing = list(result.scalars().all())

        # Filter by participants (JSONB comparison)
        for hilo in existing:
            if sorted(hilo.participantes) == sorted_participantes:
                return hilo

        # Create new thread
        hilo = HiloMensaje(
            tenant_id=tenant_id,
            asunto=asunto,
            participantes=sorted_participantes,
        )
        self.session.add(hilo)
        await self.session.flush()
        return hilo

    # ── Inbox queries ──────────────────────────────────────────────────

    async def list_inbox(
        self,
        usuario_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return paginated thread summaries with unread counts.

        Each thread summary includes:
        - hilo_id, asunto
        - ultimo_mensaje (latest message cuerpo, truncated)
        - ultima_fecha (timestamp of latest message)
        - remitente_nombre (sender's full name)
        - no_leidos (count of unread messages for this user in thread)

        Excludes threads where all messages have been soft-deleted by user.

        Args:
            usuario_id: The authenticated user's UUID.
            limit: Max items per page.
            offset: Pagination offset.

        Returns:
            Tuple of (list of thread summary dicts, total count).
        """
        # Get IDs of messages deleted by this user
        deleted_subq = (
            select(MensajeEliminado.mensaje_id)
            .where(MensajeEliminado.usuario_id == usuario_id)
            .subquery()
        )

        # First, get distinct hilo_ids where user is a participant
        # and there are visible (not deleted) messages
        hilo_stmt = (
            select(Mensaje.hilo_id)
            .where(
                Mensaje.tenant_id == self.tenant_id,
                or_(
                    Mensaje.remitente_id == usuario_id,
                    Mensaje.destinatario_id == usuario_id,
                ),
                Mensaje.id.notin_(select(deleted_subq.c.mensaje_id)),
            )
            .distinct()
        )
        result = await self.session.execute(hilo_stmt)
        hilo_ids = [row[0] for row in result.all()]

        if not hilo_ids:
            return [], 0

        # Get total count
        total = len(hilo_ids)

        # For each thread, get latest message, unread count, and other participant's name
        summaries = []
        for hilo_id in hilo_ids:
            # Get the thread
            hilo_result = await self.session.execute(
                select(HiloMensaje).where(HiloMensaje.id == hilo_id)
            )
            hilo = hilo_result.scalar_one_or_none()
            if hilo is None:
                continue

            # Get the latest visible message in this thread
            latest_msg_stmt = (
                select(Mensaje)
                .where(
                    Mensaje.hilo_id == hilo_id,
                    Mensaje.id.notin_(select(deleted_subq.c.mensaje_id)),
                )
                .order_by(Mensaje.created_at.desc())
                .limit(1)
            )
            latest_result = await self.session.execute(latest_msg_stmt)
            latest_msg = latest_result.scalar_one_or_none()
            if latest_msg is None:
                continue

            # Get unread count for this user in this thread
            unread_count = await self._count_unread_in_thread(
                hilo_id, usuario_id, deleted_subq,
            )

            # Get the "other" participant's name (the one who is not current user)
            otro_id = (
                latest_msg.remitente_id
                if latest_msg.destinatario_id == usuario_id
                else latest_msg.destinatario_id
            )
            remitente_nombre = await self._get_usuario_nombre(otro_id)

            summaries.append({
                "hilo_id": hilo_id,
                "asunto": hilo.asunto,
                "ultimo_mensaje": latest_msg.cuerpo[:120] if len(latest_msg.cuerpo) > 120 else latest_msg.cuerpo,
                "ultima_fecha": latest_msg.created_at,
                "remitente_nombre": remitente_nombre,
                "no_leidos": unread_count,
            })

        # Sort by ultima_fecha descending
        summaries.sort(key=lambda s: s["ultima_fecha"], reverse=True)

        # Apply pagination
        paginated = summaries[offset:offset + limit]

        return paginated, total

    async def _count_unread_in_thread(
        self,
        hilo_id: str,
        usuario_id: str,
        deleted_subq,
    ) -> int:
        """Count unread messages for a user in a specific thread."""
        stmt = (
            select(func.count())
            .select_from(Mensaje)
            .where(
                Mensaje.hilo_id == hilo_id,
                Mensaje.destinatario_id == usuario_id,
                Mensaje.leido.is_(False),
                Mensaje.id.notin_(select(deleted_subq.c.mensaje_id)),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _get_usuario_nombre(self, usuario_id: str) -> str:
        """Get the full name of a user by ID."""
        stmt = (
            select(Usuario)
            .where(Usuario.id == usuario_id)
        )
        result = await self.session.execute(stmt)
        usuario = result.scalar_one_or_none()
        if usuario is None:
            return "Usuario desconocido"
        return f"{usuario.nombre} {usuario.apellidos}".strip()

    # ── Thread detail ──────────────────────────────────────────────────

    async def get_thread(
        self,
        hilo_id: str,
        usuario_id: str,
    ) -> tuple[HiloMensaje | None, list[Mensaje]]:
        """Get all messages in a thread, filtered by per-user deletions.

        Args:
            hilo_id: Thread UUID.
            usuario_id: The authenticated user's UUID (for deletion filtering).

        Returns:
            Tuple of (HiloMensaje or None, list of visible Mensaje).
        """
        # Get the thread
        hilo_result = await self.session.execute(
            select(HiloMensaje).where(HiloMensaje.id == hilo_id)
        )
        hilo = hilo_result.scalar_one_or_none()
        if hilo is None:
            return None, []

        # Get IDs of messages deleted by this user
        deleted_subq = (
            select(MensajeEliminado.mensaje_id)
            .where(MensajeEliminado.usuario_id == usuario_id)
            .subquery()
        )

        # Get visible messages ordered by created_at
        stmt = (
            select(Mensaje)
            .where(
                Mensaje.hilo_id == hilo_id,
                Mensaje.id.notin_(select(deleted_subq.c.mensaje_id)),
            )
            .order_by(Mensaje.created_at.asc())
        )
        result = await self.session.execute(stmt)
        mensajes = list(result.scalars().all())

        return hilo, mensajes

    # ── Read status ────────────────────────────────────────────────────

    async def mark_as_read(self, hilo_id: str, usuario_id: str) -> None:
        """Mark all messages in a thread as read for the given user.

        Sets ``leido = True`` for messages where ``destinatario_id``
        matches the user.

        Args:
            hilo_id: Thread UUID.
            usuario_id: The user marking messages as read.
        """
        stmt = (
            update(Mensaje)
            .where(
                Mensaje.hilo_id == hilo_id,
                Mensaje.destinatario_id == usuario_id,
                Mensaje.leido.is_(False),
            )
            .values(leido=True)
        )
        await self.session.execute(stmt)

    async def count_no_leidos(self, usuario_id: str) -> int:
        """Count unread messages for a user.

        Args:
            usuario_id: The user's UUID.

        Returns:
            Number of unread messages.
        """
        # Get IDs of messages deleted by this user
        deleted_subq = (
            select(MensajeEliminado.mensaje_id)
            .where(MensajeEliminado.usuario_id == usuario_id)
            .subquery()
        )

        stmt = (
            select(func.count())
            .select_from(Mensaje)
            .where(
                Mensaje.tenant_id == self.tenant_id,
                Mensaje.destinatario_id == usuario_id,
                Mensaje.leido.is_(False),
                Mensaje.id.notin_(select(deleted_subq.c.mensaje_id)),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    # ── Soft delete ────────────────────────────────────────────────────

    async def soft_delete_for_user(self, mensaje_id: str, usuario_id: str) -> None:
        """Create a deletion record so the message is hidden from the user.

        Args:
            mensaje_id: Message UUID.
            usuario_id: The user who wants to hide the message.
        """
        # Check if already deleted
        stmt = (
            select(MensajeEliminado)
            .where(
                MensajeEliminado.mensaje_id == mensaje_id,
                MensajeEliminado.usuario_id == usuario_id,
            )
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is not None:
            return  # Already deleted

        delete_record = MensajeEliminado(
            mensaje_id=mensaje_id,
            usuario_id=usuario_id,
        )
        self.session.add(delete_record)
        await self.session.flush()

    # ── Participant validation ─────────────────────────────────────────

    async def get_hilo_participants(self, hilo_id: str) -> list[str]:
        """Get the list of participant UUIDs for a thread.

        Args:
            hilo_id: Thread UUID.

        Returns:
            List of participant UUID strings.
        """
        result = await self.session.execute(
            select(HiloMensaje).where(HiloMensaje.id == hilo_id)
        )
        hilo = result.scalar_one_or_none()
        if hilo is None:
            return []
        return hilo.participantes

    async def user_is_participant(self, hilo_id: str, usuario_id: str) -> bool:
        """Check if a user is a participant in a thread.

        Args:
            hilo_id: Thread UUID.
            usuario_id: User UUID.

        Returns:
            True if the user is a participant.
        """
        result = await self.session.execute(
            select(HiloMensaje).where(HiloMensaje.id == hilo_id)
        )
        hilo = result.scalar_one_or_none()
        if hilo is None:
            return False
        return usuario_id in hilo.participantes

    async def set_ultimo_mensaje_at(self, hilo_id: str) -> None:
        """Update the ultimo_mensaje_at timestamp on a thread.

        Args:
            hilo_id: Thread UUID.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(HiloMensaje)
            .where(HiloMensaje.id == hilo_id)
            .values(ultimo_mensaje_at=now)
        )
        await self.session.execute(stmt)
