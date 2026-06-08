"""Service layer for Tarea internal task management (C-16).

Encapsulates business logic:
- Task assignment with trazability
- Forward-only state transitions (Pendiente -> En progreso -> Resuelta)
- Cancelacion desde cualquier estado
- Authorization: quien puede cambiar estado
- Comment management
"""

import logging

from fastapi import HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from app.core.unit_of_work import UnitOfWork
from app.models.tarea import ComentarioTarea, EstadoTarea, Tarea
from app.schemas.tarea import (
    ComentarioCreate,
    ComentarioRead,
    TareaCreate,
    TareaEstadoUpdate,
    TareaFilter,
    TareaRead,
    TareaReadAdmin,
)

logger = logging.getLogger(__name__)

# ── Valid transitions matrix ─────────────────────────────────────────────

_VALID_TRANSITIONS: dict[str, set[str]] = {
    EstadoTarea.PENDIENTE.value: {EstadoTarea.EN_PROGRESO.value, EstadoTarea.CANCELADA.value},
    EstadoTarea.EN_PROGRESO.value: {EstadoTarea.RESUELTA.value, EstadoTarea.CANCELADA.value},
    EstadoTarea.RESUELTA.value: {EstadoTarea.CANCELADA.value},
    EstadoTarea.CANCELADA.value: set(),  # Terminal state — no transitions out
}


def _is_valid_transition(from_estado: str, to_estado: str) -> bool:
    """Check if a state transition is valid per the state machine.

    Args:
        from_estado: Current estado value.
        to_estado: Desired new estado value.

    Returns:
        ``True`` if the transition is allowed.
    """
    allowed = _VALID_TRANSITIONS.get(from_estado, set())
    return to_estado in allowed


def _validar_transicion_estado(from_estado: str, to_estado: str) -> None:
    """Validate a state transition, raising HTTPException(422) if invalid.

    Args:
        from_estado: Current estado value.
        to_estado: Desired new estado value.

    Raises:
        HTTPException(422): If the transition is not allowed.
    """
    if to_estado == from_estado:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Transicion no permitida: la tarea ya esta en estado '{from_estado}'",
        )
    if not _is_valid_transition(from_estado, to_estado):
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Transicion no permitida: de '{from_estado}' a '{to_estado}'. "
                f"Los estados solo avanzan hacia adelante "
                f"(Pendiente -> En progreso -> Resuelta). "
                f"Cancelada es permitida desde cualquier estado."
            ),
        )


def _puede_cambiar_estado(
    user_id: str,
    asignado_a: str,
    roles: list[str],
    tiene_permiso_admin: bool,
) -> bool:
    """Check if a user has permission to change a task's estado.

    Permission is granted if:
    1. The user is the assigned user (``asignado_a``), OR
    2. The user has the ``tareas:admin`` permission

    Args:
        user_id: The authenticated user's UUID.
        asignado_a: The task's assigned user UUID.
        roles: The user's role list (unused here, reserved for future rules).
        tiene_permiso_admin: Whether the user has ``tareas:admin``.

    Returns:
        ``True`` if the user may change the estado.
    """
    return user_id == asignado_a or tiene_permiso_admin


# ── Service class ────────────────────────────────────────────────────────


class TareaService:
    """Business logic for tarea management.

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
        self.repo = uow.tarea  # backward compat alias

    # ── Create tarea ───────────────────────────────────────────────────

    async def create_tarea(self, data: TareaCreate) -> Tarea:
        """Assign a new task to a user.

        Args:
            data: The task creation data.

        Returns:
            The created Tarea instance.

        Raises:
            HTTPException(404): If the referenced materia does not exist
                in the current tenant (only if materia_id is provided).
        """
        create_data = data.model_dump(exclude_unset=True)
        create_data["asignado_por"] = self.current_user["id"]

        # Validate materia exists if provided
        if create_data.get("materia_id"):
            materia = await self.uow.materia.get_by_id(create_data["materia_id"])
            if materia is None:
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Materia no encontrada en el tenant actual",
                )

        tarea = await self.repo.create(create_data)
        logger.info(
            "Tarea %s created by %s for user %s",
            tarea.id, self.current_user["id"], data.asignado_a,
        )
        return tarea

    # ── Change estado ──────────────────────────────────────────────────

    async def change_estado(
        self,
        tarea_id: str,
        data: TareaEstadoUpdate,
    ) -> Tarea:
        """Change the estado of a tarea with validation.

        Validates:
        1. The tarea exists and belongs to the current tenant.
        2. The state transition is valid (forward-only + cancel).
        3. The user has permission to change estado.

        Args:
            tarea_id: The Tarea UUID.
            data: The new estado value.

        Returns:
            The updated Tarea instance.

        Raises:
            HTTPException(404): If tarea not found.
            HTTPException(403): If user lacks permission.
            HTTPException(422): If state transition is invalid.
        """
        tarea = await self.repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )

        # Validate transition
        _validar_transicion_estado(tarea.estado, data.estado)

        # Check permission
        roles = self.current_user.get("roles", [])
        user_id = self.current_user["id"]
        tiene_admin = self._check_permission("tareas:admin")

        if not _puede_cambiar_estado(user_id, tarea.asignado_a, roles, tiene_admin):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="No tienes permiso para cambiar el estado de esta tarea",
            )

        updated = await self.repo.update_estado(tarea_id, data.estado)
        logger.info(
            "Tarea %s estado changed: %s -> %s by %s",
            tarea_id, tarea.estado, data.estado, user_id,
        )
        return updated  # type: ignore[return-value]

    # ── Add comment ────────────────────────────────────────────────────

    async def add_comentario(
        self,
        tarea_id: str,
        data: ComentarioCreate,
    ) -> ComentarioTarea:
        """Add an immutable comment to a tarea.

        Args:
            tarea_id: The Tarea UUID.
            data: The comment text.

        Returns:
            The created ComentarioTarea instance.

        Raises:
            HTTPException(404): If tarea not found.
        """
        tarea = await self.repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )

        comentario = await self.repo.add_comentario({
            "tarea_id": tarea_id,
            "autor_id": self.current_user["id"],
            "texto": data.texto,
        })
        return comentario

    # ── Get my tasks ───────────────────────────────────────────────────

    async def get_mis_tareas(
        self,
        filters: TareaFilter,
    ) -> list[Tarea]:
        """Get tasks assigned to the authenticated user.

        Args:
            filters: Optional estado and materia_id filters.

        Returns:
            List of Tarea instances assigned to the current user.
        """
        return await self.repo.list_by_asignado(
            asignado_a=self.current_user["id"],
            estado=filters.estado,
            materia_id=filters.materia_id,
        )

    # ── Admin: get all tasks ───────────────────────────────────────────

    async def get_admin_tareas(
        self,
        filters: TareaFilter,
    ) -> list[dict]:
        """Get all tasks in the tenant with admin filters.

        Returns enriched data with comment counts.

        Args:
            filters: Conjunctive filters (estado, materia_id, asignado_a,
                asignado_por, q).

        Returns:
            List of dicts with task data plus ``comentario_count``.
        """
        tareas = await self.repo.list_all(
            estado=filters.estado,
            materia_id=filters.materia_id,
            asignado_a=filters.asignado_a,
            asignado_por=filters.asignado_por,
            q=filters.q,
        )

        result = []
        for t in tareas:
            count = await self.repo.get_comentario_count(t.id)
            tarea_dict = {
                "id": t.id,
                "tenant_id": t.tenant_id,
                "materia_id": t.materia_id,
                "asignado_a": t.asignado_a,
                "asignado_por": t.asignado_por,
                "estado": t.estado,
                "descripcion": t.descripcion,
                "contexto_id": t.contexto_id,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
                "comentario_count": count,
            }
            result.append(tarea_dict)

        return result

    # ── Helpers ────────────────────────────────────────────────────────

    def _check_permission(self, permission: str) -> bool:
        """Check if the current user has a specific permission.

        Args:
            permission: The permission string to check.

        Returns:
            ``True`` if the user has the permission.
        """
        from app.core.permissions import require_permission

        roles = self.current_user.get("roles", [])
        checker = require_permission(permission)
        return checker(roles)
