"""Generic BaseRepository[T] with automatic tenant scoping and soft-delete filtering.

Provides the standard CRUD operations (get, list, create, update, soft_delete)
with automatic ``WHERE tenant_id = ...`` and ``WHERE estado != 'Inactivo'``
filtering for models that have those attributes.

Usage::

    # For a model with tenant_id + AuditMixin
    repo = BaseRepository[Usuario](session=session, tenant_id="tenant-a")
    user = await repo.get("user-uuid")

    # For a model without tenant_id (e.g., Tenant itself)
    tenant_repo = BaseRepository[Tenant](session=session, tenant_id=None)
    all_tenants = await tenant_repo.list()
"""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import AppModel
from app.models.mixins import AuditMixin, EstadoRegistro

T = TypeVar("T", bound=AppModel)


class BaseRepository(Generic[T]):
    """Generic repository with optional tenant scoping and soft-delete filtering.

    Args:
        session: An active SQLAlchemy ``AsyncSession``.
        tenant_id: Optional tenant UUID string. If set, all queries are
            automatically scoped to this tenant for models that have
            a ``tenant_id`` attribute.
    """

    def __init__(self, session: AsyncSession, tenant_id: str | None = None):
        self.session = session
        self.tenant_id = tenant_id
        self._model_class: type[T] | None = None

    @property
    def model_class(self) -> type[T]:
        """Return the bound model class (resolved from ``Generic[T]``)."""
        if self._model_class is not None:
            return self._model_class
        # Try to resolve from Generic[T] at runtime
        if hasattr(self, "__orig_class__"):
            orig = self.__orig_class__
            if hasattr(orig, "__args__") and orig.__args__:
                self._model_class = orig.__args__[0]
                return self._model_class  # type: ignore[return-value]
        raise TypeError(
            "Cannot resolve model_class from Generic parameter. "
            "Either subclass BaseRepository and set model_class, "
            "or use the class directly with type parameter."
        )

    @model_class.setter
    def model_class(self, value: type[T]) -> None:
        self._model_class = value

    # ── Query helpers ────────────────────────────────────────────────

    def _stmt(self) -> Select:
        """Return a base ``SELECT`` statement with automatic scoping.

        - For models with ``tenant_id``, adds ``WHERE tenant_id = ...``
        - For models with ``AuditMixin`` (``estado``), adds
          ``WHERE estado != 'Inactivo'`` (excludes soft-deleted records)

        Subclasses can override this method to customize query scoping.
        """
        model = self.model_class
        stmt = select(model)

        # Tenant scope
        if self.tenant_id is not None and hasattr(model, "tenant_id"):
            stmt = stmt.where(model.tenant_id == self.tenant_id)  # type: ignore[union-attr]

        # Exclude soft-deleted (estado = 'Inactivo')
        if issubclass(model, AuditMixin):
            stmt = stmt.where(model.estado != EstadoRegistro.INACTIVO)  # type: ignore[union-attr]

        return stmt

    # ── CRUD operations ──────────────────────────────────────────────

    async def get(self, id: str) -> T | None:
        """Retrieve an entity by primary key, scoped by tenant.

        Args:
            id: The UUID string of the entity.

        Returns:
            The entity instance, or ``None`` if not found or soft-deleted.
        """
        model = self.model_class
        stmt = self._stmt().where(model.id == id)  # type: ignore[union-attr]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, **filters: Any) -> list[T]:
        """List entities with optional equality filters.

        Results are automatically scoped by tenant (if ``tenant_id`` was set)
        and exclude soft-deleted records.

        Args:
            **filters: Optional keyword arguments for equality filtering.
                E.g., ``list(estado=EstadoRegistro.ACTIVO)``.

        Returns:
            A list of entity instances (empty list if none found).
        """
        model = self.model_class
        stmt = self._stmt()
        for attr, value in filters.items():
            column = getattr(model, attr, None)
            if column is not None:
                stmt = stmt.where(column == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: dict | BaseModel) -> T:
        """Create a new entity.

        If ``tenant_id`` is set and the model has a ``tenant_id`` attribute,
        the tenant is automatically assigned.

        Args:
            data: A dictionary or Pydantic model with the entity attributes.

        Returns:
            The newly created entity instance (after flush, not committed).

        Raises:
            TypeError: If ``data`` is neither a ``dict`` nor a ``BaseModel``.
        """
        model = self.model_class
        if isinstance(data, BaseModel):
            data = data.model_dump()
        elif not isinstance(data, dict):
            raise TypeError(f"Expected dict or BaseModel, got {type(data)}")

        # Auto-assign tenant_id
        if self.tenant_id is not None and hasattr(model, "tenant_id"):
            data.setdefault("tenant_id", self.tenant_id)

        instance = model(**data)  # type: ignore[call-arg]
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, id: str, data: dict | BaseModel) -> T | None:
        """Partially update an entity by primary key.

        Only the fields present in ``data`` are updated. The ``updated_at``
        timestamp is updated automatically via SQLAlchemy's ``onupdate``.

        Args:
            id: The UUID string of the entity to update.
            data: A dictionary or Pydantic model with the fields to update.

        Returns:
            The updated entity instance, or ``None`` if not found.
        """
        model = self.model_class
        if isinstance(data, BaseModel):
            data = data.model_dump(exclude_unset=True)
        elif not isinstance(data, dict):
            raise TypeError(f"Expected dict or BaseModel, got {type(data)}")

        stmt = (
            update(model)
            .where(model.id == id)  # type: ignore[union-attr]
            .values(**data)
            .returning(model)
        )
        if self.tenant_id is not None and hasattr(model, "tenant_id"):
            stmt = stmt.where(model.tenant_id == self.tenant_id)  # type: ignore[union-attr]
        if issubclass(model, AuditMixin):
            stmt = stmt.where(model.estado != EstadoRegistro.INACTIVO)  # type: ignore[union-attr]

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_delete(self, id: str) -> None:
        """Soft-delete an entity by setting ``estado='Inactivo'`` and ``deleted_at=now()``.

        Args:
            id: The UUID string of the entity to soft-delete.

        Raises:
            ValueError: If the entity is not found or already inactive.
        """
        model = self.model_class
        now = datetime.now(timezone.utc)

        stmt = (
            update(model)
            .where(model.id == id)  # type: ignore[union-attr]
            .values(
                estado=EstadoRegistro.INACTIVO,
                deleted_at=now,
            )
            .returning(model)
        )
        if self.tenant_id is not None and hasattr(model, "tenant_id"):
            stmt = stmt.where(model.tenant_id == self.tenant_id)  # type: ignore[union-attr]
        if issubclass(model, AuditMixin):
            stmt = stmt.where(model.estado != EstadoRegistro.INACTIVO)  # type: ignore[union-attr]

        result = await self.session.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise ValueError(
                f"Entity {model.__name__}[{id}] not found or already inactive."
            )
