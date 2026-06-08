"""Service layer for Guardia management with business rules.

Encapsulates business logic:
- Guardia registration with cross-tenant validation
- Guardia query with optional estado and date range filters
"""

from datetime import date

from fastapi import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from app.core.unit_of_work import UnitOfWork
from app.schemas.guardias import GuardiaCreate, GuardiaResponse


class GuardiaService:
    """Business logic for Guardia CRUD and queries."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.tenant_id = uow._tenant_id or ""

    async def registrar_guardia(self, data: GuardiaCreate) -> GuardiaResponse:
        """Register a new guardia record.

        Args:
            data: The guardia creation data.

        Returns:
            The created GuardiaResponse.

        Raises:
            HTTPException(404): If the referenced materia is not found.
        """
        # Verify materia exists in tenant
        materia = await self.uow.materia.get_by_id(data.materia_id)
        if materia is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Materia not found",
            )

        instance = await self.uow.guardia.create(data.model_dump(exclude_unset=True))
        return GuardiaResponse.model_validate(instance)

    async def listar_guardias(
        self,
        materia_id: str,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[GuardiaResponse]:
        """List guardias with optional filters.

        Args:
            materia_id: The materia UUID to filter by.
            estado: Optional estado filter (Pendiente, Realizada, Cancelada).
            fecha_desde: Optional start date filter.
            fecha_hasta: Optional end date filter.

        Returns:
            A list of GuardiaResponse objects.
        """
        instances = await self.uow.guardia.list_by_materia(
            materia_id=materia_id,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        return [GuardiaResponse.model_validate(i) for i in instances]
