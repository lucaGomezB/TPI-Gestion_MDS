"""Service layer for internal messaging (C-13).

Encapsulates business logic for:
- Sending messages with thread creation/reuse
- Replying within existing threads
- Inbox listing with pagination
- Thread viewing with auto-mark-read
- Unread message counting
"""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from app.core.unit_of_work import UnitOfWork
from app.schemas.mensaje import (
    HiloResponse,
    InboxItemResponse,
    InboxResponse,
    MensajeCreatedResponse,
    MensajeCreate,
    MensajeResponse,
    MensajeResponder,
    NoLeidosResponse,
)

logger = logging.getLogger(__name__)


class MensajeService:
    """Business logic for internal messaging.

    Args:
        uow: The ``UnitOfWork`` instance for data access.
        current_user: Authenticated user dict (id, tenant_id, roles).
    """

    def __init__(
        self,
        uow: UnitOfWork,
        current_user: dict,
    ):
        self.uow = uow
        self.tenant_id = uow._tenant_id or ""
        self.current_user = current_user

    async def enviar(self, data: MensajeCreate) -> MensajeCreatedResponse:
        """Send a message to another user in the same tenant.

        1. Validates that the recipient exists and belongs to the same tenant.
        2. Finds or creates a thread for this conversation.
        3. Creates the message with leido = False.

        Args:
            data: Validated message creation data.

        Returns:
            MensajeCreatedResponse with the new message and thread data.

        Raises:
            HTTPException(404): If recipient not found or in different tenant.
        """
        usuario_id = self.current_user["id"]

        # Validate recipient exists and belongs to same tenant
        destinatario = await self._validate_recipient(data.destinatario_id)

        # Find or create thread
        participantes = sorted([usuario_id, destinatario.id])
        hilo = await self.uow.mensaje.find_or_create_hilo(
            tenant_id=self.tenant_id,
            participantes=participantes,
            asunto=data.asunto,
        )

        # Create the message
        now = datetime.now(timezone.utc)
        mensaje_data = {
            "tenant_id": self.tenant_id,
            "hilo_id": hilo.id,
            "remitente_id": usuario_id,
            "destinatario_id": destinatario.id,
            "asunto": data.asunto,
            "cuerpo": data.cuerpo.strip(),
            "leido": False,
        }
        mensaje = await self.uow.mensaje.create(mensaje_data)

        # Update thread's last message timestamp
        await self.uow.mensaje.set_ultimo_mensaje_at(hilo.id)

        logger.info(
            "Message %s sent from %s to %s in thread %s",
            mensaje.id, usuario_id, destinatario.id, hilo.id,
        )

        return MensajeCreatedResponse(
            id=mensaje.id,
            hilo_id=hilo.id,
            asunto=mensaje.asunto,
            created_at=mensaje.created_at,
        )

    async def responder(
        self,
        mensaje_id: str,
        data: MensajeResponder,
    ) -> MensajeCreatedResponse:
        """Reply within an existing thread.

        The ``mensaje_id`` references an existing Mensaje to identify
        the thread (via hilo_id). The current user must be a participant.

        Args:
            mensaje_id: UUID of an existing message in the thread.
            data: Reply body.

        Returns:
            MensajeCreatedResponse for the new message.

        Raises:
            HTTPException(404): If the referenced message is not found.
            HTTPException(403): If user is not a participant in the thread.
        """
        usuario_id = self.current_user["id"]

        # Get the referenced message to find the thread
        mensaje_ref = await self.uow.mensaje.get(mensaje_id)
        if mensaje_ref is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        hilo_id = mensaje_ref.hilo_id

        # Verify user is a participant
        if not await self.uow.mensaje.user_is_participant(hilo_id, usuario_id):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="You are not a participant in this thread",
            )

        # Get participants to determine the other party
        participantes = await self.uow.mensaje.get_hilo_participants(hilo_id)
        otro_id = next(
            (p for p in participantes if p != usuario_id),
            None,
        )
        if otro_id is None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Cannot determine message recipient",
            )

        # Create the reply
        mensaje_data = {
            "tenant_id": self.tenant_id,
            "hilo_id": hilo_id,
            "remitente_id": usuario_id,
            "destinatario_id": otro_id,
            "asunto": mensaje_ref.asunto,
            "cuerpo": data.cuerpo.strip(),
            "leido": False,
        }
        reply = await self.uow.mensaje.create(mensaje_data)

        # Update thread's last message timestamp
        await self.uow.mensaje.set_ultimo_mensaje_at(hilo_id)

        logger.info(
            "Reply %s sent by %s in thread %s",
            reply.id, usuario_id, hilo_id,
        )

        return MensajeCreatedResponse(
            id=reply.id,
            hilo_id=hilo_id,
            asunto=reply.asunto,
            created_at=reply.created_at,
        )

    async def listar_inbox(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> InboxResponse:
        """List inbox threads for the authenticated user.

        Args:
            limit: Max items per page.
            offset: Pagination offset.

        Returns:
            InboxResponse with paginated thread summaries.
        """
        usuario_id = self.current_user["id"]

        items, total = await self.uow.mensaje.list_inbox(
            usuario_id=usuario_id,
            limit=limit,
            offset=offset,
        )

        data = [InboxItemResponse.model_validate(item) for item in items]

        return InboxResponse(
            data=data,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def ver_hilo(self, mensaje_id: str) -> HiloResponse:
        """View a complete thread by a message ID.

        Finds the thread by resolving the message's hilo_id.
        Auto-marks messages as read for the current user.

        Args:
            mensaje_id: UUID of any message in the thread.

        Returns:
            HiloResponse with all messages in the thread.

        Raises:
            HTTPException(403): If user is not a participant.
            HTTPException(404): If message not found.
        """
        usuario_id = self.current_user["id"]

        # Get the message to find the thread
        mensaje_ref = await self.uow.mensaje.get(mensaje_id)
        if mensaje_ref is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        hilo_id = mensaje_ref.hilo_id

        # Verify user is a participant
        if not await self.uow.mensaje.user_is_participant(hilo_id, usuario_id):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="You are not a participant in this thread",
            )

        # Get thread messages (filtered by per-user deletions)
        hilo, mensajes = await self.uow.mensaje.get_thread(hilo_id, usuario_id)

        if hilo is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Thread not found",
            )

        # Auto-mark messages as read for this user
        await self.uow.mensaje.mark_as_read(hilo_id, usuario_id)

        mensajes_response = [
            MensajeResponse(
                id=m.id,
                hilo_id=m.hilo_id,
                remitente_id=m.remitente_id,
                destinatario_id=m.destinatario_id,
                asunto=m.asunto,
                cuerpo=m.cuerpo,
                leido=m.leido,
                created_at=m.created_at,
            )
            for m in mensajes
        ]

        return HiloResponse(
            hilo_id=hilo.id,
            asunto=hilo.asunto,
            participantes=hilo.participantes,
            mensajes=mensajes_response,
        )

    async def contar_no_leidos(self) -> NoLeidosResponse:
        """Count unread messages for the authenticated user.

        Returns:
            NoLeidosResponse with the unread count.
        """
        count = await self.uow.mensaje.count_no_leidos(self.current_user["id"])
        return NoLeidosResponse(count=count)

    # ── Helpers ────────────────────────────────────────────────────────

    async def _validate_recipient(self, destinatario_id: str):
        """Validate that the recipient exists and belongs to the same tenant.

        Args:
            destinatario_id: The proposed recipient UUID.

        Returns:
            The Usuario instance.

        Raises:
            HTTPException(404): If user not found or in different tenant.
        """
        from app.models.usuario import Usuario

        # Get the raw repository for user lookup (without tenant scope)
        from app.repositories.base import BaseRepository

        user_repo = BaseRepository[Usuario](self.uow._session)
        user_repo.model_class = Usuario

        usuario = await user_repo.get(destinatario_id)
        if usuario is None or usuario.tenant_id != self.tenant_id:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Recipient not found",
            )
        return usuario
