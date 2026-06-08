"""Repository layer for salary grid — SalarioBase, SalarioPlus, GrupoMateria, MateriaGrupo.

Provides CRUD operations with tenant scoping and specialized queries:
- Vigente queries (records active on a given date)
- Overlap detection for temporal validity
- Materia assignment via MateriaGrupo join table
"""

from datetime import date
from typing import Any

from sqlalchemy import Select, delete, select, update
from sqlalchemy.orm import joinedload

from app.models.grilla_salarial import GrupoMateria, MateriaGrupo, SalarioBase, SalarioPlus
from app.repositories.base import BaseRepository


class SalarioBaseRepository(BaseRepository[SalarioBase]):
    """CRUD for SalarioBase with overlap detection and vigente queries."""

    async def get_vigente_for_rol(
        self, rol: str, target_date: date
    ) -> SalarioBase | None:
        """Return the active SalarioBase for a given role on a specific date.

        A record is vigente if: ``desde <= target_date AND (hasta IS NULL OR hasta >= target_date)``
        """
        model = self.model_class
        stmt: Select = (
            select(model)
            .where(model.tenant_id == self.tenant_id)
            .where(model.rol == rol)
            .where(model.desde <= target_date)
            .where((model.hasta.is_(None)) | (model.hasta >= target_date))
            .order_by(model.desde.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def check_overlap(
        self,
        rol: str,
        desde: date,
        hasta: date | None,
        exclude_id: str | None = None,
    ) -> bool:
        """Check if a SalarioBase record overlaps with existing records for the same role.

        Two date ranges overlap if::
            existing.desde < new.hasta AND new.desde < existing.hasta
        where NULL hasta is treated as infinite future.

        Args:
            rol: The role to check.
            desde: New record's start date.
            hasta: New record's end date (None = open-ended).
            exclude_id: Optional ID to exclude from the check (for updates).

        Returns:
            True if an overlap exists, False otherwise.
        """
        model = self.model_class
        stmt: Select = select(model).where(
            model.tenant_id == self.tenant_id,
            model.rol == rol,
            model.desde < (hasta or date(9999, 12, 31)),
            desde < (model.hasta or date(9999, 12, 31)),
        )
        if exclude_id:
            stmt = stmt.where(model.id != exclude_id)  # type: ignore[union-attr]

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


class SalarioPlusRepository(BaseRepository[SalarioPlus]):
    """CRUD for SalarioPlus with overlap detection and vigente queries."""

    async def get_vigentes_for_grupo(
        self, grupo: str, rol: str, target_date: date
    ) -> list[SalarioPlus]:
        """Return active SalarioPlus records for a specific grupo+rol on a date."""
        model = self.model_class
        stmt: Select = (
            select(model)
            .where(model.tenant_id == self.tenant_id)
            .where(model.grupo == grupo)
            .where(model.rol == rol)
            .where(model.desde <= target_date)
            .where((model.hasta.is_(None)) | (model.hasta >= target_date))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_vigentes_for_date(
        self, target_date: date
    ) -> list[SalarioPlus]:
        """Return ALL active SalarioPlus records for a given date (consumed by C-19)."""
        model = self.model_class
        stmt: Select = (
            select(model)
            .where(model.tenant_id == self.tenant_id)
            .where(model.desde <= target_date)
            .where((model.hasta.is_(None)) | (model.hasta >= target_date))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def check_overlap(
        self,
        grupo: str,
        rol: str,
        desde: date,
        hasta: date | None,
        exclude_id: str | None = None,
    ) -> bool:
        """Check if a SalarioPlus record overlaps with existing records for the same grupo+rol."""
        model = self.model_class
        stmt: Select = select(model).where(
            model.tenant_id == self.tenant_id,
            model.grupo == grupo,
            model.rol == rol,
            model.desde < (hasta or date(9999, 12, 31)),
            desde < (model.hasta or date(9999, 12, 31)),
        )
        if exclude_id:
            stmt = stmt.where(model.id != exclude_id)  # type: ignore[union-attr]

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


class GrupoMateriaRepository(BaseRepository[GrupoMateria]):
    """CRUD for GrupoMateria with materia assignment operations."""

    async def get_with_materias(self, id: str) -> GrupoMateria | None:
        """Get a GrupoMateria with its associated materias eagerly loaded."""
        model = self.model_class
        stmt: Select = (
            select(model)
            .options(joinedload(model.materias))
            .where(model.id == id)
            .where(model.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def assign_materias(
        self, grupo_id: str, materia_ids: list[str]
    ) -> list[MateriaGrupo]:
        """Assign multiple materias to a group.

        Removes any existing assignments not in the list (replace semantics)
        and creates new MateriaGrupo records for each materia_id.

        Args:
            grupo_id: The UUID of the GrupoMateria.
            materia_ids: List of materia UUIDs to assign.

        Returns:
            The list of MateriaGrupo records.
        """
        # Remove existing assignments not in the new list
        existing = await self.get_materias_by_grupo(grupo_id)
        existing_ids = {mg.materia_id for mg in existing}
        to_remove = existing_ids - set(materia_ids)
        if to_remove:
            await self._remove_materias(grupo_id, list(to_remove))

        # Add new assignments
        new_ids = set(materia_ids) - existing_ids
        created: list[MateriaGrupo] = []
        for materia_id in new_ids:
            mg = MateriaGrupo(
                tenant_id=self.tenant_id,
                materia_id=materia_id,
                grupo_id=grupo_id,
            )
            self.session.add(mg)
            created.append(mg)

        if new_ids:
            await self.session.flush()

        return await self.get_materias_by_grupo(grupo_id)

    async def get_materias_by_grupo(self, grupo_id: str) -> list[MateriaGrupo]:
        """Get all MateriaGrupo records for a given group."""
        stmt: Select = (
            select(MateriaGrupo)
            .where(MateriaGrupo.grupo_id == grupo_id)
            .where(MateriaGrupo.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _remove_materias(self, grupo_id: str, materia_ids: list[str]) -> None:
        """Remove specific materia assignments from a group."""
        stmt = (
            delete(MateriaGrupo)
            .where(MateriaGrupo.grupo_id == grupo_id)
            .where(MateriaGrupo.materia_id.in_(materia_ids))
        )
        await self.session.execute(stmt)
