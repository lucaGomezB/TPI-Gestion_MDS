"""Repository for padron de alumnos (VersionPadron / EntradaPadron).

Extends BaseRepository with padron-specific query methods:
- get_active_version: find the active version for a (materia, cohorte)
- get_entries: list all entries for a version
- deactivate_version: set activa=False on a version
- create_version: create a new active version
- create_entries: bulk insert entries for a version
- get_version_history: list all versions for a materia with entry counts
- get_active_entries: get entries via the active version
"""

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.base import BaseRepository


class PadronRepository(BaseRepository[VersionPadron]):
    """Tenant-scoped repository for padron operations.

    Args:
        session: An active SQLAlchemy ``AsyncSession``.
        tenant_id: The tenant UUID string for data isolation.
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = VersionPadron

    # ── Version queries ──────────────────────────────────────────────

    async def get_active_version(
        self, materia_id: str, cohorte_id: str
    ) -> VersionPadron | None:
        """Find the active version for a (materia, cohorte) within the tenant.

        Args:
            materia_id: The materia UUID.
            cohorte_id: The cohorte UUID.

        Returns:
            The active ``VersionPadron``, or ``None`` if none exists.
        """
        stmt = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.cohorte_id == cohorte_id,
                VersionPadron.activa == True,  # noqa: E712
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_version_history(self, materia_id: str) -> list[VersionPadron]:
        """List all versions for a materia with total_entradas, ordered by created_at desc.

        Args:
            materia_id: The materia UUID.

        Returns:
            A list of ``VersionPadron`` instances ordered by created_at descending.
        """
        stmt = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
            )
            .order_by(VersionPadron.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate_version(self, version_id: str) -> None:
        """Set ``activa=False`` on a version.

        Args:
            version_id: The version UUID to deactivate.
        """
        stmt = (
            update(VersionPadron)
            .where(
                VersionPadron.id == version_id,
                VersionPadron.tenant_id == self.tenant_id,
            )
            .values(activa=False)
        )
        await self.session.execute(stmt)

    async def create_version(self, data: dict) -> VersionPadron:
        """Create a new active version.

        Automatically sets tenant_id and activa=True.

        Args:
            data: Dictionary with version attributes (materia_id, cohorte_id,
                cargado_por).

        Returns:
            The newly created ``VersionPadron`` instance.
        """
        data.setdefault("tenant_id", self.tenant_id)
        data.setdefault("activa", True)
        data.setdefault("total_entradas", 0)
        return await self.create(data)

    # ── Entry queries ────────────────────────────────────────────────

    async def get_entries(self, version_id: str) -> list[EntradaPadron]:
        """List all entries for a version.

        Args:
            version_id: The version UUID.

        Returns:
            A list of ``EntradaPadron`` instances.
        """
        stmt = (
            select(EntradaPadron)
            .where(
                EntradaPadron.version_id == version_id,
                EntradaPadron.tenant_id == self.tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_entries(self, materia_id: str) -> list[EntradaPadron]:
        """Get entries from the active version for a materia.

        Args:
            materia_id: The materia UUID.

        Returns:
            A list of ``EntradaPadron`` instances from the active version,
            or an empty list if no active version exists.
        """
        # Find all active versions for this materia
        stmt_version = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.activa == True,  # noqa: E712
            )
        )
        result = await self.session.execute(stmt_version)
        active_version = result.scalar_one_or_none()
        if active_version is None:
            return []

        # Get entries from active version
        stmt_entries = (
            select(EntradaPadron)
            .where(
                EntradaPadron.version_id == active_version.id,
                EntradaPadron.tenant_id == self.tenant_id,
            )
        )
        entries_result = await self.session.execute(stmt_entries)
        return list(entries_result.scalars().all())

    async def create_entries(
        self, version_id: str, entries_data: list[dict]
    ) -> int:
        """Bulk insert entries for a version.

        Args:
            version_id: The version UUID to associate entries with.
            entries_data: List of dicts with entry attributes (nombre, apellidos,
                email, comision, regional).

        Returns:
            The number of entries created.
        """
        for entry in entries_data:
            entry.setdefault("tenant_id", self.tenant_id)
            entry["version_id"] = version_id

        # Bulk insert
        if entries_data:
            self.session.add_all(
                [EntradaPadron(**entry) for entry in entries_data]
            )
            await self.session.flush()

            # Update total_entradas count on the version
            stmt_update = (
                update(VersionPadron)
                .where(VersionPadron.id == version_id)
                .values(total_entradas=len(entries_data))
            )
            await self.session.execute(stmt_update)

        return len(entries_data)
