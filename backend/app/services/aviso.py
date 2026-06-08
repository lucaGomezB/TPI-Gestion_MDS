"""Service layer for avisos (C-12).

Encapsulates business logic for:
- Admin CRUD with validation
- Visibility filtering (RN-18, RN-20)
- Acknowledgment (RN-19)
- Scope-based access control
"""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.core.unit_of_work import UnitOfWork
from app.schemas.aviso import (
    AckResponse,
    AvisoCreate,
    AvisoListResponse,
    AvisoResponse,
    AvisoUpdate,
)

logger = logging.getLogger(__name__)


class AvisoService:
    """Business logic for the avisos system.

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

    # ── Admin CRUD ────────────────────────────────────────────────────

    async def create_aviso(self, data: AvisoCreate) -> AvisoResponse:
        """Create a new aviso (admin).

        Args:
            data: Validated aviso creation data.

        Returns:
            AvisoResponse for the created aviso.
        """
        aviso = await self.uow.aviso.create(data.model_dump())
        logger.info(
            "Aviso %s created by user %s",
            aviso.id, self.current_user["id"],
        )
        return AvisoResponse.model_validate(aviso)

    async def list_avisos_admin(
        self,
        activo: bool | None = None,
        alcance: str | None = None,
        severidad: str | None = None,
    ) -> AvisoListResponse:
        """List avisos with optional filters (admin).

        Args:
            activo: Filter by active status.
            alcance: Filter by alcance.
            severidad: Filter by severidad.

        Returns:
            Paginated list response.
        """
        avisos = await self.uow.aviso.list_with_filters(
            activo=activo,
            alcance=alcance,
            severidad=severidad,
        )
        items = [AvisoResponse.model_validate(a) for a in avisos]
        return AvisoListResponse(items=items, total=len(items))

    async def get_aviso_detail(self, aviso_id: str) -> AvisoResponse:
        """Get aviso detail with ack count (admin).

        Args:
            aviso_id: Aviso UUID.

        Returns:
            AvisoResponse with ack_count.

        Raises:
            HTTPException(404): If not found.
        """
        aviso, ack_count = await self.uow.aviso.get_with_ack_count(aviso_id)
        if aviso is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Aviso not found",
            )
        response = AvisoResponse.model_validate(aviso)
        response.ack_count = ack_count
        return response

    async def update_aviso(self, aviso_id: str, data: AvisoUpdate) -> AvisoResponse:
        """Update an existing aviso (admin).

        Args:
            aviso_id: Aviso UUID.
            data: Fields to update.

        Returns:
            Updated AvisoResponse.

        Raises:
            HTTPException(404): If not found.
        """
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            # Return existing without changes
            aviso, ack_count = await self.uow.aviso.get_with_ack_count(aviso_id)
            if aviso is None:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail="Aviso not found",
                )
            response = AvisoResponse.model_validate(aviso)
            response.ack_count = ack_count
            return response

        aviso = await self.uow.aviso.update(aviso_id, update_data)
        if aviso is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Aviso not found",
            )
        logger.info("Aviso %s updated by user %s", aviso_id, self.current_user["id"])
        return AvisoResponse.model_validate(aviso)

    async def deactivate_aviso(self, aviso_id: str) -> None:
        """Soft-deactivate an aviso (admin, sets activo=False).

        Args:
            aviso_id: Aviso UUID.

        Raises:
            HTTPException(404): If not found.
        """
        aviso = await self.uow.aviso.get(aviso_id)
        if aviso is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Aviso not found",
            )
        aviso.activo = False
        logger.info(
            "Aviso %s deactivated by user %s",
            aviso_id, self.current_user["id"],
        )

    # ── User visibility (RN-18, RN-20) ─────────────────────────────────

    async def list_avisos_visibles(
        self,
        severidad: str | None = None,
    ) -> list[AvisoResponse]:
        """Get avisos visible to the current user (RN-18, RN-20).

        Args:
            severidad: Optional severity filter.

        Returns:
            List of visible AvisoResponse instances.
        """
        usuario_id = self.current_user["id"]
        roles = self.current_user.get("roles", [])

        avisos = await self.uow.aviso.find_visibles(
            usuario_id=usuario_id,
            roles=roles,
            severidad_filter=severidad,
        )
        return [AvisoResponse.model_validate(a) for a in avisos]

    # ── Acknowledgment (RN-19) ─────────────────────────────────────────

    async def acknowledge_aviso(self, aviso_id: str) -> AckResponse:
        """Acknowledge reading an aviso (RN-19).

        Validates:
        - Aviso exists and is visible to the user.
        - Aviso has requiere_ack=True.
        - Idempotency: if already acknowledged, return existing.

        Args:
            aviso_id: Aviso UUID.

        Returns:
            AckResponse with acknowledgment timestamp.

        Raises:
            HTTPException(404): If aviso not found or not visible.
            HTTPException(400): If aviso does not require ack.
        """
        usuario_id = self.current_user["id"]
        roles = self.current_user.get("roles", [])

        # Find visible avisos (includes tenant + vigencia + scope check)
        avisos = await self.uow.aviso.find_visibles(
            usuario_id=usuario_id,
            roles=roles,
        )
        aviso = next((a for a in avisos if a.id == aviso_id), None)

        if aviso is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Aviso not found",
            )

        if not aviso.requiere_ack:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="This aviso does not require acknowledgment",
            )

        # Check existing acknowledgment (idempotency)
        existing = await self.uow.acknowledgment.find_by_aviso_and_user(
            aviso_id=aviso_id,
            usuario_id=usuario_id,
        )
        if existing is not None:
            return AckResponse(
                acknowledged=True,
                leido_en=existing.leido_en,
            )

        # Create new acknowledgment
        now = datetime.now(timezone.utc)
        ack_data = {
            "aviso_id": aviso_id,
            "usuario_id": usuario_id,
            "leido_en": now,
        }
        await self.uow.acknowledgment.create(ack_data)
        logger.info(
            "Aviso %s acknowledged by user %s",
            aviso_id, usuario_id,
        )
        return AckResponse(
            acknowledged=True,
            leido_en=now,
        )
