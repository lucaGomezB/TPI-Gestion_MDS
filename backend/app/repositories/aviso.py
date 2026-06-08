"""AvisoRepository — tenant-scoped CRUD with admin filters and visibility queries.

Supports:
- Admin filters: activo, alcance, severidad
- Visibility queries: vigencia range, scope filtering (RN-20)
- Acknowledgment counts via join
"""

from datetime import datetime, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.aviso import Aviso
from app.repositories.base import BaseRepository


class AvisoRepository(BaseRepository[Aviso]):
    """Tenant-scoped CRUD for Aviso with admin filters and visibility queries."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(session, tenant_id)
        self.model_class = Aviso

    # ── Admin queries ─────────────────────────────────────────────────

    def _admin_stmt(self) -> Select:
        """Base stmt for admin queries (no soft-delete, uses activo)."""
        model = self.model_class
        stmt = select(model)
        if self.tenant_id is not None:
            stmt = stmt.where(model.tenant_id == self.tenant_id)
        return stmt

    async def list_with_filters(
        self,
        activo: bool | None = None,
        alcance: str | None = None,
        severidad: str | None = None,
    ) -> list[Aviso]:
        """List avisos with optional admin filters.

        Args:
            activo: Filter by active status.
            alcance: Filter by alcance value.
            severidad: Filter by severidad value.

        Returns:
            List of Aviso instances ordered by orden ASC, created_at DESC.
        """
        model = self.model_class
        stmt = self._admin_stmt()

        if activo is not None:
            stmt = stmt.where(model.activo == activo)
        if alcance is not None:
            stmt = stmt.where(model.alcance == alcance)
        if severidad is not None:
            stmt = stmt.where(model.severidad == severidad)

        stmt = stmt.order_by(model.orden.asc(), model.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_ack_count(self, id: str) -> tuple[Aviso | None, int]:
        """Get aviso with acknowledgment count.

        Args:
            id: Aviso UUID.

        Returns:
            Tuple of (Aviso instance or None, ack_count).
        """
        model = self.model_class
        stmt = self._admin_stmt().where(model.id == id)
        result = await self.session.execute(stmt)
        aviso = result.scalar_one_or_none()

        if aviso is None:
            return None, 0

        # Count acknowledgments
        count_stmt = (
            select(func.count())
            .select_from(AcknowledgmentAviso)
            .where(AcknowledgmentAviso.aviso_id == id)
        )
        count_result = await self.session.execute(count_stmt)
        ack_count = count_result.scalar() or 0
        return aviso, ack_count

    # ── Visibility queries (RN-18, RN-20) ─────────────────────────────

    async def find_visibles(
        self,
        usuario_id: str,
        roles: list[str],
        alcance_filter: str | None = None,
        severidad_filter: str | None = None,
    ) -> list[Aviso]:
        """Find avisos visible to a user based on alcance and vigencia (RN-18, RN-20).

        Args:
            usuario_id: The user's UUID.
            roles: The user's role names.
            alcance_filter: Optional alcance filter.
            severidad_filter: Optional severidad filter.

        Returns:
            List of visible Aviso instances ordered by orden ASC, created_at DESC.
        """
        model = self.model_class
        now = datetime.now(timezone.utc)

        stmt = (
            select(model)
            .where(
                model.tenant_id == self.tenant_id,
                model.activo.is_(True),
                model.inicio_en <= now,
                model.fin_en >= now,
            )
            .order_by(model.orden.asc(), model.created_at.desc())
        )

        if alcance_filter:
            stmt = stmt.where(model.alcance == alcance_filter)
        if severidad_filter:
            stmt = stmt.where(model.severidad == severidad_filter)

        result = await self.session.execute(stmt)
        all_avisos = list(result.scalars().all())

        # Apply scope filtering in Python (RN-20)
        # Global: visible to all
        # PorRol: filter by rol_destino matching user roles
        # PorMateria / PorCohorte: requires checking user assignments
        visible: list[Aviso] = []
        for aviso in all_avisos:
            if aviso.alcance == "Global":
                visible.append(aviso)
            elif aviso.alcance == "PorRol":
                if aviso.rol_destino and aviso.rol_destino in roles:
                    visible.append(aviso)
            elif aviso.alcance == "PorMateria":
                if await self._user_has_materia(usuario_id, aviso.materia_id):
                    visible.append(aviso)
            elif aviso.alcance == "PorCohorte":
                if await self._user_has_cohorte(usuario_id, aviso.cohorte_id):
                    visible.append(aviso)

        return visible

    async def _user_has_materia(self, usuario_id: str, materia_id: str | None) -> bool:
        """Check if a user has an active assignment to a materia."""
        if materia_id is None:
            return False
        from app.models.asignacion import Asignacion

        stmt = (
            select(Asignacion)
            .where(
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.usuario_id == usuario_id,
                Asignacion.materia_id == materia_id,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _user_has_cohorte(self, usuario_id: str, cohorte_id: str | None) -> bool:
        """Check if a user has assignments in a cohorte."""
        if cohorte_id is None:
            return False
        from app.models.asignacion import Asignacion

        stmt = (
            select(Asignacion)
            .where(
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.usuario_id == usuario_id,
                Asignacion.cohorte_id == cohorte_id,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
