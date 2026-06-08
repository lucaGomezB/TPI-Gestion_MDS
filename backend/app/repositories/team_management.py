"""AsignacionRepository — tenant-scoped CRUD with equipo-level queries.

Provides:
- Standard CRUD via ``BaseRepository``
- ``list_by_filters`` — filtered list with optional vigencia state filter
- ``bulk_create`` — multiple assignments in one transaction
- ``find_by_equipo`` / ``find_vigentes_by_equipo`` — equipo-scoped queries
- ``update_vigencia`` — bulk vigencia date update
- ``export_equipo_data`` — joined query with Usuario data for CSV export
"""

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.asignacion import Asignacion
from app.models.usuario import Usuario
from app.repositories.base import BaseRepository


class AsignacionRepository(BaseRepository[Asignacion]):
    """Tenant-scoped CRUD for Asignacion with equipo-level operations.

    Per D-14, this is the single repository for all assignment operations.
    Since Asignacion does NOT inherit AuditMixin (D-01), BaseRepository's
    soft-delete filter does not apply — all records are always visible.
    """

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = Asignacion

    # ── Filtered list ─────────────────────────────────────────────────

    async def list_by_filters(
        self,
        usuario_id: str | None = None,
        materia_id: str | None = None,
        carrera_id: str | None = None,
        cohorte_id: str | None = None,
        rol: str | None = None,
        vigente: bool | None = None,
    ) -> list[Asignacion]:
        """List assignments with optional filters.

        Args:
            usuario_id: Filter by user.
            materia_id: Filter by subject.
            carrera_id: Filter by academic program.
            cohorte_id: Filter by cohort.
            rol: Filter by role string.
            vigente: If True, only currently vigente; if False, only expired;
                if None, all.

        Returns:
            List of matching Asignacion instances.
        """
        model = self.model_class
        stmt = self._stmt()

        if usuario_id is not None:
            stmt = stmt.where(model.usuario_id == usuario_id)
        if materia_id is not None:
            stmt = stmt.where(model.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(model.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(model.cohorte_id == cohorte_id)
        if rol is not None:
            stmt = stmt.where(model.rol == rol)

        # Vigencia state filter (applied at DB level for performance)
        today = date.today()
        if vigente is True:
            stmt = stmt.where(
                model.vig_desde <= today,
                (model.vig_hasta.is_(None)) | (model.vig_hasta >= today),
            )
        elif vigente is False:
            stmt = stmt.where(model.vig_hasta.is_not(None), model.vig_hasta < today)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Bulk operations ───────────────────────────────────────────────

    async def bulk_create(self, entries: list[dict]) -> list[Asignacion]:
        """Create multiple assignments in a single transaction.

        Args:
            entries: List of dicts with Asignacion field values.

        Returns:
            List of created Asignacion instances (flushed, not committed).
        """
        instances = []
        for data in entries:
            data.setdefault("tenant_id", self.tenant_id)
            instance = Asignacion(**data)
            self.session.add(instance)
            instances.append(instance)
        await self.session.flush()
        return instances

    # ── Equipo-scoped queries ─────────────────────────────────────────

    async def find_by_equipo(
        self,
        materia_id: str | None,
        carrera_id: str | None,
        cohorte_id: str | None,
    ) -> list[Asignacion]:
        """Find all assignments for an academic context.

        All three parameters are required to form a complete equipo scope.
        """
        model = self.model_class
        stmt = self._stmt().where(
            model.materia_id == materia_id,
            model.carrera_id == carrera_id,
            model.cohorte_id == cohorte_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_vigentes_by_equipo(
        self,
        materia_id: str | None,
        carrera_id: str | None,
        cohorte_id: str | None,
    ) -> list[Asignacion]:
        """Find only currently vigente assignments for an academic context.

        An assignment is vigente if ``vig_desde <= today`` AND
        (``vig_hasta IS NULL`` OR ``vig_hasta >= today``).
        """
        model = self.model_class
        today = date.today()
        stmt = (
            self._stmt()
            .where(
                model.materia_id == materia_id,
                model.carrera_id == carrera_id,
                model.cohorte_id == cohorte_id,
                model.vig_desde <= today,
            )
            .where((model.vig_hasta.is_(None)) | (model.vig_hasta >= today))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Bulk vigencia update ──────────────────────────────────────────

    async def update_vigencia(
        self,
        materia_id: str | None,
        carrera_id: str | None,
        cohorte_id: str | None,
        vig_desde: date,
        vig_hasta: date | None,
    ) -> int:
        """Update vigencia dates for all assignments matching the equipo scope.

        Args:
            materia_id: Filter by materia.
            carrera_id: Filter by carrera.
            cohorte_id: Filter by cohorte.
            vig_desde: New start date.
            vig_hasta: New end date (None = indefinite).

        Returns:
            Number of updated rows.
        """
        model = self.model_class
        stmt = self._stmt()
        if materia_id is not None:
            stmt = stmt.where(model.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(model.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(model.cohorte_id == cohorte_id)

        # Fetch matching records and update
        result = await self.session.execute(stmt)
        instances: list[Asignacion] = list(result.scalars().all())
        for inst in instances:
            inst.vig_desde = vig_desde
            inst.vig_hasta = vig_hasta
        await self.session.flush()
        return len(instances)

    # ── Export query ───────────────────────────────────────────────────

    async def export_equipo_data(
        self,
        materia_id: str | None,
        carrera_id: str | None,
        cohorte_id: str | None,
    ) -> list[tuple[Asignacion, Usuario, Usuario | None]]:
        """Return assignments joined with Usuario data for CSV export.

        Since ``Asignacion`` does not declare SQLAlchemy ``relationship()``
        attributes, we fetch users in a second query keyed by ID.

        Returns:
            List of tuples ``(asignacion, usuario, responsable)`` where
            ``responsable`` is the supervisor Usuario (or None).
        """
        model = self.model_class
        stmt = (
            select(model)
            .where(model.tenant_id == self.tenant_id)
        )
        if materia_id is not None:
            stmt = stmt.where(model.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(model.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(model.cohorte_id == cohorte_id)

        result = await self.session.execute(stmt)
        rows: list[Asignacion] = list(result.scalars().all())

        # Collect all referenced user IDs
        user_ids: set[str] = set()
        for a in rows:
            user_ids.add(a.usuario_id)
            if a.responsable_id:
                user_ids.add(a.responsable_id)

        if not user_ids:
            return []

        user_result = await self.session.execute(
            select(Usuario).where(
                Usuario.id.in_(list(user_ids)),
                Usuario.tenant_id == self.tenant_id,
            )
        )
        users: dict[str, Usuario] = {u.id: u for u in user_result.scalars().all()}

        result_list: list[tuple[Asignacion, Usuario, Usuario | None]] = []
        for a in rows:
            usuario = users.get(a.usuario_id)
            responsable = users.get(a.responsable_id) if a.responsable_id else None
            if usuario:
                result_list.append((a, usuario, responsable))

        return result_list
