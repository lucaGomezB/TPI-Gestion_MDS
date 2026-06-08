"""Service layer for the communications queue (C-11).

Encapsulates business logic for:
- Template preview (RN-16)
- Enqueue bulk communications (RN-16, RN-17)
- Approval flow (RN-17)
- Cancellation
- Materia access verification for PROFESOR scope enforcement
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from app.core.unit_of_work import UnitOfWork
from app.models.materia import Materia
from app.models.padron import EntradaPadron
from app.models.comunicacion import (
    EstadoComunicacion,
    EstadoLote,
)
from app.models.tenant import Tenant
from app.schemas.communication import (
    AprobarRequest,
    ComunicacionResponse,
    EnviarRequest,
    LoteResponse,
    PreviewItem,
    PreviewRequest,
    PreviewResponse,
)
from app.services.email_sender import _mask_email
from app.services.template_engine import build_preview_context, render_template

logger = logging.getLogger(__name__)


class CommunicationService:
    """Business logic for the communications queue.

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

    # ── Public API ─────────────────────────────────────────────────────

    async def preview_comunicacion(
        self,
        materia_id: str,
        body: PreviewRequest,
    ) -> PreviewResponse:
        """Preview rendered templates for sample recipients (RN-16).

        Validates materia access, fetches sample EntradaPadron entries,
        renders templates, and returns preview items.

        Args:
            materia_id: Target materia UUID.
            body: Preview request with template strings.

        Returns:
            PreviewResponse with rendered previews.

        Raises:
            HTTPException(403): If user lacks materia access.
            HTTPException(404): If materia or padron entries not found.
        """
        await self._check_materia_access(materia_id)

        materia = await self._get_materia(materia_id)

        # Fetch padron entries
        entries = await self._get_padron_entries(materia_id, body.alumno_ids)

        if not entries:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="No student entries found for this materia",
            )

        previews: list[PreviewItem] = []
        for entry in entries[:5]:  # Max 5 previews
            alumno_nombre = f"{entry.nombre} {entry.apellidos}".strip()
            context = build_preview_context(
                alumno_nombre=alumno_nombre,
                materia_nombre=materia.nombre,
            )
            asunto_rendered = render_template(body.asunto, context)
            cuerpo_rendered = render_template(body.cuerpo, context)
            previews.append(PreviewItem(
                alumno_nombre=alumno_nombre,
                email_preview=_mask_email(entry.email),
                asunto_renderizado=asunto_rendered,
                cuerpo_renderizado=cuerpo_rendered,
            ))

        return PreviewResponse(previews=previews)

    async def enqueue_comunicacion(
        self,
        materia_id: str,
        body: EnviarRequest,
    ) -> LoteResponse:
        """Enqueue a bulk communication for sending (RN-16, RN-17).

        1. Validates materia access.
        2. Checks preview_confirmado is True (RN-16).
        3. Checks tenant approval config (RN-17).
        4. Creates Lote + Comunicaciones.
        5. Encrypts email addresses.

        Args:
            materia_id: Target materia UUID.
            body: Enviar request with templates and confirmation.

        Returns:
            LoteResponse for the created batch.

        Raises:
            HTTPException(400): If preview not confirmed.
            HTTPException(403): If user lacks materia access.
            HTTPException(404): If materia not found.
        """
        await self._check_materia_access(materia_id)

        # RN-16: preview_confirmado MUST be True
        if not body.preview_confirmado:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="preview_confirmado is required before sending (RN-16)",
            )

        materia = await self._get_materia(materia_id)

        # Fetch target entries
        entries = await self._get_padron_entries(materia_id, body.alumno_ids)
        if not entries:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="No student entries found for this materia",
            )

        # RN-17: Check tenant approval config
        requiere_aprobacion = await self._get_tenant_approval_config()

        # Create the lote
        lote_data = {
            "materia_id": materia_id,
            "enviado_por": self.current_user["id"],
            "asunto": body.asunto,
            "total": len(entries),
            "estado": (
                EstadoLote.aprobacion_pendiente.value
                if requiere_aprobacion
                else EstadoLote.pendiente.value
            ),
            "requiere_aprobacion": requiere_aprobacion,
            "preview_confirmado": True,
        }
        lote = await self.uow.lote.create(lote_data)

        # Build communication entries
        com_entries = []
        for entry in entries:
            alumno_nombre = f"{entry.nombre} {entry.apellidos}".strip()
            context = build_preview_context(
                alumno_nombre=alumno_nombre,
                materia_nombre=materia.nombre,
            )
            com_entries.append({
                "lote_id": lote.id,
                "materia_id": materia_id,
                "enviado_por": self.current_user["id"],
                "destinatario": entry.email,  # EncryptedString handles encryption
                "asunto": render_template(body.asunto, context),
                "cuerpo": render_template(body.cuerpo, context),
                "estado": EstadoComunicacion.pendiente.value,
            })

        await self.uow.comunicacion.bulk_create(com_entries)

        logger.info(
            "Enqueued %d communications for materia %s (lote=%s, aprobacion=%s)",
            len(entries), materia_id, lote.id, requiere_aprobacion,
        )

        return LoteResponse.model_validate(lote)

    async def listar_comunicaciones(
        self,
        materia_id: str,
    ) -> list[LoteResponse]:
        """List all lote batches for a materia.

        Args:
            materia_id: Target materia UUID.

        Returns:
            List of LoteResponse.

        Raises:
            HTTPException(403): If user lacks materia access.
        """
        await self._check_materia_access(materia_id)
        lotes = await self.uow.lote.find_by_materia(materia_id)
        return [LoteResponse.model_validate(l) for l in lotes]

    async def get_lote_detail(
        self,
        materia_id: str,
        lote_id: str,
    ) -> LoteResponse:
        """Get a specific lote with its communications.

        Args:
            materia_id: Target materia UUID.
            lote_id: Lote UUID.

        Returns:
            LoteResponse with count details.

        Raises:
            HTTPException(404): If lote not found.
        """
        await self._check_materia_access(materia_id)
        lote = await self.uow.lote.get(lote_id)
        if lote is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Lote not found",
            )
        return LoteResponse.model_validate(lote)

    async def aprobar_comunicacion(
        self,
        lote_id: str,
        body: AprobarRequest,
    ) -> dict:
        """Approve or reject a pending bulk communication (RN-17).

        Args:
            lote_id: Lote UUID.
            body: Approval decision (aprobar/rechazar) with optional motivo.

        Returns:
            Dict with id, estado, mensaje.

        Raises:
            HTTPException(404): If lote not found.
            HTTPException(400): If lote not in approval state.
        """
        lote = await self.uow.lote.get(lote_id)
        if lote is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Lote not found",
            )

        if lote.estado != EstadoLote.aprobacion_pendiente.value:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Lote is not pending approval",
            )

        if body.accion.value == "aprobar":
            lote.estado = EstadoLote.enviando.value
            lote.aprobado_por = self.current_user["id"]
            lote.aprobado_at = datetime.now(timezone.utc)

            logger.info("Lote %s approved by %s", lote_id, self.current_user["id"])
            return {
                "id": lote.id,
                "estado": lote.estado,
                "mensaje": "Communication batch approved and queued for sending",
            }

        # Reject
        lote.estado = EstadoLote.cancelado.value
        lote.aprobado_por = self.current_user["id"]
        lote.aprobado_at = datetime.now(timezone.utc)

        # Cancel all pending communications in this lote
        await self.uow.comunicacion.cancel_by_lote(lote_id)

        logger.info(
            "Lote %s rejected by %s. Reason: %s",
            lote_id, self.current_user["id"], body.motivo,
        )
        return {
            "id": lote.id,
            "estado": lote.estado,
            "mensaje": f"Communication batch rejected. Motivo: {body.motivo or 'N/A'}",
        }

    async def cancelar_comunicacion(
        self,
        comunicacion_id: str,
    ) -> ComunicacionResponse:
        """Cancel a single pending communication.

        Only communications in Pendiente state can be cancelled.

        Args:
            comunicacion_id: Communication UUID.

        Returns:
            ComunicacionResponse with updated state.

        Raises:
            HTTPException(404): If communication not found.
            HTTPException(400): If not in Pendiente state.
        """
        com = await self.uow.comunicacion.get(comunicacion_id)
        if com is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Communication not found",
            )

        if com.estado != EstadoComunicacion.pendiente.value:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Only pending communications can be cancelled",
            )

        com.estado = EstadoComunicacion.cancelado.value

        return ComunicacionResponse.model_validate(com)

    # ── Helpers ────────────────────────────────────────────────────────

    async def _check_materia_access(self, materia_id: str) -> None:
        """Verify the current user has access to the materia.

        For PROFESOR role: checks that the user has an active Asignacion
        for the materia. For COORDINADOR/ADMIN: always allowed within tenant.

        Raises:
            HTTPException(403): If access is denied.
        """
        roles = self.current_user.get("roles", [])
        user_id = self.current_user["id"]

        # COORDINADOR and ADMIN have full access
        if any(r in roles for r in ("COORDINADOR", "ADMIN")):
            return

        # PROFESOR: must have active assignment to this materia
        asignaciones = await self.uow.asignacion.list_by_filters(
            usuario_id=user_id,
            materia_id=materia_id,
            rol="PROFESOR",
        )

        if not asignaciones:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="You do not have access to this materia",
            )

    async def _get_materia(self, materia_id: str) -> Materia:
        """Fetch a materia, raising 404 if not found.

        Args:
            materia_id: Materia UUID.

        Returns:
            The Materia instance.

        Raises:
            HTTPException(404): If materia not found.
        """
        materia = await self.uow.materia.get_by_id(materia_id)
        if materia is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Materia not found",
            )
        return materia

    async def _get_padron_entries(
        self,
        materia_id: str,
        alumno_ids: list[str] | None = None,
    ) -> list[EntradaPadron]:
        """Fetch EntradaPadron entries for a materia via active version.

        Queries through VersionPadron to find entries belonging to the
        active version for the given materia.

        Args:
            materia_id: Materia UUID.
            alumno_ids: Optional list of specific usuario IDs to filter by.

        Returns:
            List of EntradaPadron instances.
        """
        from sqlalchemy import select
        from app.models.padron import EntradaPadron, VersionPadron

        stmt = (
            select(EntradaPadron)
            .join(VersionPadron, EntradaPadron.version_id == VersionPadron.id)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.activa.is_(True),
            )
        )
        if alumno_ids:
            stmt = stmt.where(EntradaPadron.usuario_id.in_(alumno_ids))

        result = await self.uow._session.execute(stmt)
        return list(result.scalars().all())

    async def _get_tenant_approval_config(self) -> bool:
        """Read the ``requiere_aprobacion_masiva`` flag from tenant config.

        Returns:
            True if bulk communications require approval (RN-17), else False.
        """
        from sqlalchemy import select

        result = await self.uow._session.execute(
            select(Tenant).where(Tenant.id == self.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            return False
        return tenant.configuracion.get("comunicaciones", {}).get(
            "requiere_aprobacion_masiva", False
        )
