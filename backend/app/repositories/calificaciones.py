"""Repository for calificaciones (grades) and UmbralMateria (thresholds).

Extends BaseRepository with grade-specific query methods:
- get_active_version_for_materia: find active padron version for a materia
- get_threshold: get UmbralMateria for an (asignacion, materia)
- upsert_threshold: create or update UmbralMateria
- bulk_create_calificaciones: bulk insert grade records
- get_calificaciones: list grades with optional filters
- delete_calificaciones_scope: scope-isolated delete
"""

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificaciones import Calificacion, UmbralMateria
from app.models.padron import VersionPadron
from app.repositories.base import BaseRepository


class CalificacionesRepository(BaseRepository[Calificacion]):
    """Tenant-scoped repository for grade operations.

    Args:
        session: An active SQLAlchemy ``AsyncSession``.
        tenant_id: The tenant UUID string for data isolation.
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = Calificacion

    # ── Padron version queries ────────────────────────────────────────

    async def get_active_version_for_materia(
        self, materia_id: str
    ) -> VersionPadron | None:
        """Find the active padron version for a materia.

        Args:
            materia_id: The materia UUID.

        Returns:
            The active ``VersionPadron``, or ``None`` if none exists.
        """
        stmt = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.activa == True,  # noqa: E712
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Threshold queries ─────────────────────────────────────────────

    async def get_threshold(
        self, asignacion_id: str, materia_id: str
    ) -> UmbralMateria | None:
        """Get the UmbralMateria for an (asignacion, materia).

        Args:
            asignacion_id: The asignacion UUID.
            materia_id: The materia UUID.

        Returns:
            The ``UmbralMateria`` instance, or ``None`` if not configured.
        """
        stmt = (
            select(UmbralMateria)
            .where(
                UmbralMateria.tenant_id == self.tenant_id,
                UmbralMateria.asignacion_id == asignacion_id,
                UmbralMateria.materia_id == materia_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_threshold(
        self, data: dict
    ) -> UmbralMateria:
        """Create or update an UmbralMateria.

        Uses the unique constraint (asignacion_id, materia_id) to determine
        whether to create or update.

        Args:
            data: Dict with keys: asignacion_id, materia_id, umbral_pct,
                valores_aprobatorios, tenant_id.

        Returns:
            The created or updated ``UmbralMateria`` instance.
        """
        # Check if threshold already exists
        existing = await self.get_threshold(
            data["asignacion_id"], data["materia_id"]
        )
        if existing:
            # Update existing
            stmt = (
                update(UmbralMateria)
                .where(UmbralMateria.id == existing.id)
                .values(
                    umbral_pct=data.get("umbral_pct", existing.umbral_pct),
                    valores_aprobatorios=(
                        data.get("valores_aprobatorios")
                        if "valores_aprobatorios" in data
                        else existing.valores_aprobatorios
                    ),
                )
                .returning(UmbralMateria)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one()

        # Create new
        data.setdefault("tenant_id", self.tenant_id)
        instance = UmbralMateria(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    # ── Grade CRUD ────────────────────────────────────────────────────

    async def bulk_create_calificaciones(
        self, entries: list[dict]
    ) -> int:
        """Bulk insert grade records.

        Args:
            entries: List of dicts with Calificacion attributes.

        Returns:
            The number of records created.
        """
        for entry in entries:
            entry.setdefault("tenant_id", self.tenant_id)
            entry.setdefault("origen", "Importado")

        if entries:
            self.session.add_all(
                [Calificacion(**entry) for entry in entries]
            )
            await self.session.flush()

        return len(entries)

    async def get_calificaciones(
        self, materia_id: str, filters: dict | None = None
    ) -> list[Calificacion]:
        """List grade records for a materia with optional filters.

        Args:
            materia_id: The materia UUID.
            filters: Optional dict with keys ``actividad`` and/or ``aprobado``.

        Returns:
            A list of ``Calificacion`` instances.
        """
        filters = filters or {}
        stmt = (
            select(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
            )
        )

        if "actividad" in filters and filters["actividad"]:
            stmt = stmt.where(Calificacion.actividad == filters["actividad"])
        if "aprobado" in filters and filters["aprobado"] is not None:
            stmt = stmt.where(Calificacion.aprobado == filters["aprobado"])

        stmt = stmt.order_by(Calificacion.importado_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_calificaciones_scope(
        self, materia_id: str, cargado_por: str | None = None
    ) -> int:
        """Delete grade records with scope isolation.

        Args:
            materia_id: The materia UUID.
            cargado_por: If set (PROFESOR), only deletes records with this
                ``cargado_por``. If None (COORDINADOR/ADMIN), deletes all
                records for the materia.

        Returns:
            The number of deleted records.
        """
        stmt = (
            delete(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
            )
        )
        if cargado_por is not None:
            stmt = stmt.where(Calificacion.cargado_por == cargado_por)

        result = await self.session.execute(stmt)
        return result.rowcount
