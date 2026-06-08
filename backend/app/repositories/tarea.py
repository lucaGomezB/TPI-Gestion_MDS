"""Repository for Tarea and ComentarioTarea CRUD operations.

Extends ``BaseRepository[T]`` with tenant-scoped queries for:
- Listing tasks by assigned user
- Admin listing with conjunctive filters (estado, materia_id, asignado_a, q)
- Estado updates
- Comment management
"""

from sqlalchemy import func, select, update

from app.models.tarea import ComentarioTarea, Tarea
from app.repositories.base import BaseRepository


class TareaRepository(BaseRepository[Tarea]):
    """Tenant-scoped repository for Tarea CRUD with specialized queries.

    All queries are automatically scoped to the repository's ``tenant_id``
    via the inherited ``_stmt()`` method.
    """

    model_class = Tarea

    async def list_by_asignado(
        self,
        asignado_a: str,
        estado: str | None = None,
        materia_id: str | None = None,
    ) -> list[Tarea]:
        """List tasks assigned to a specific user, with optional filters.

        Args:
            asignado_a: The assigned user's UUID.
            estado: Optional estado filter.
            materia_id: Optional materia UUID filter.

        Returns:
            List of Tarea instances matching the criteria.
        """
        stmt = (
            self._stmt()
            .where(Tarea.asignado_a == asignado_a)
            .order_by(Tarea.created_at.desc())
        )
        if estado is not None:
            stmt = stmt.where(Tarea.estado == estado)
        if materia_id is not None:
            stmt = stmt.where(Tarea.materia_id == materia_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(
        self,
        estado: str | None = None,
        materia_id: str | None = None,
        asignado_a: str | None = None,
        asignado_por: str | None = None,
        q: str | None = None,
    ) -> list[Tarea]:
        """List all tasks in the tenant with optional conjunctive filters.

        Args:
            estado: Filter by estado.
            materia_id: Filter by materia UUID.
            asignado_a: Filter by assigned user UUID.
            asignado_por: Filter by assigner user UUID.
            q: Free-text search in descripcion (case-insensitive).

        Returns:
            List of Tarea instances matching all provided filters.
        """
        stmt = self._stmt().order_by(Tarea.created_at.desc())

        if estado is not None:
            stmt = stmt.where(Tarea.estado == estado)
        if materia_id is not None:
            stmt = stmt.where(Tarea.materia_id == materia_id)
        if asignado_a is not None:
            stmt = stmt.where(Tarea.asignado_a == asignado_a)
        if asignado_por is not None:
            stmt = stmt.where(Tarea.asignado_por == asignado_por)
        if q is not None:
            stmt = stmt.where(Tarea.descripcion.ilike(f"%{q}%"))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, id: str) -> Tarea | None:
        """Get a single tarea by its ID (tenant-scoped).

        Args:
            id: The Tarea UUID.

        Returns:
            The Tarea instance or ``None`` if not found.
        """
        return await self.get(id)

    async def update_estado(self, id: str, estado: str) -> Tarea | None:
        """Update only the estado field of a tarea.

        Args:
            id: The Tarea UUID.
            estado: The new estado value.

        Returns:
            The updated Tarea instance or ``None`` if not found.
        """
        stmt = (
            update(Tarea)
            .where(Tarea.id == id)
            .where(Tarea.tenant_id == self.tenant_id)
            .values(estado=estado)
            .returning(Tarea)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_comentario(self, data: dict) -> ComentarioTarea:
        """Add a comment to a tarea.

        Args:
            data: Dictionary with ``tarea_id``, ``autor_id``, ``texto``,
                and optionally ``tenant_id``.

        Returns:
            The created ComentarioTarea instance.
        """
        if "tenant_id" not in data and self.tenant_id is not None:
            data["tenant_id"] = self.tenant_id
        instance = ComentarioTarea(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_comentarios(self, tarea_id: str) -> list[ComentarioTarea]:
        """Get all comments for a tarea, ordered by creation time.

        Args:
            tarea_id: The Tarea UUID.

        Returns:
            List of ComentarioTarea instances.
        """
        stmt = (
            select(ComentarioTarea)
            .where(
                ComentarioTarea.tarea_id == tarea_id,
                ComentarioTarea.tenant_id == self.tenant_id,
            )
            .order_by(ComentarioTarea.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_comentario_count(self, tarea_id: str) -> int:
        """Get the number of comments for a tarea.

        Args:
            tarea_id: The Tarea UUID.

        Returns:
            Comment count.
        """
        stmt = (
            select(func.count())
            .select_from(ComentarioTarea)
            .where(
                ComentarioTarea.tarea_id == tarea_id,
                ComentarioTarea.tenant_id == self.tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
