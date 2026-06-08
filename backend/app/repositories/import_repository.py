"""Repository for manual import persistence operations.

Handles saving imported activities, grades, and enrollment data
during confirmed manual imports.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mixins import EstadoRegistro


class ImportRepository:
    """Repository for persisting manually imported grade and enrollment data."""

    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def save_imported_activities(
        self,
        dictado_id: str,
        activities: list[dict[str, Any]],
    ) -> int:
        """Save detected activities from an imported file.

        Args:
            dictado_id: The target dictado UUID.
            activities: List of activity dicts with name, scale_type, etc.

        Returns:
            Number of activities saved.
        """
        model_class = self._get_actividad_model()
        count = 0
        for act in activities:
            instance = model_class(
                tenant_id=self.tenant_id,
                dictado_id=dictado_id,
                nombre=act.get("nombre", "Unknown"),
                tipo_escala=act.get("tipo_escala", "numeric"),
                puntaje_maximo=act.get("puntaje_maximo"),
            )
            self.session.add(instance)
            count += 1

        await self.session.flush()
        return count

    async def save_imported_grades(
        self,
        grades: list[dict[str, Any]],
    ) -> int:
        """Save imported grade records.

        Args:
            grades: List of grade dicts with actividad_id, alumno_id,
                   valor_numerico, valor_textual.

        Returns:
            Number of grades saved.
        """
        model_class = self._get_calificacion_model()
        count = 0
        for grade in grades:
            instance = model_class(
                tenant_id=self.tenant_id,
                actividad_id=grade.get("actividad_id"),
                alumno_id=grade.get("alumno_id"),
                valor_numerico=grade.get("valor_numerico"),
                valor_textual=grade.get("valor_textual"),
            )
            self.session.add(instance)
            count += 1

        await self.session.flush()
        return count

    async def replace_enrollment(
        self,
        dictado_id: str,
        student_ids: list[str],
    ) -> int:
        """Destructive replacement of enrollment roster (RN-05).

        Students in the new list are enrolled. Students not in the new list
        are soft-deleted.

        Args:
            dictado_id: The target dictado UUID.
            student_ids: List of internal alumno UUIDs to enroll.

        Returns:
            Number of active enrollments.
        """
        model_class = self._get_alumno_dictado_model()

        # Get existing enrollments
        result = await self.session.execute(
            select(model_class).where(
                model_class.tenant_id == self.tenant_id,  # type: ignore[union-attr]
                model_class.dictado_id == dictado_id,  # type: ignore[union-attr]
                model_class.estado != EstadoRegistro.INACTIVO,  # type: ignore[union-attr]
            )
        )
        existing_rows = list(result.scalars().all())
        existing_ids = {getattr(row, "alumno_id") for row in existing_rows}

        # Soft-delete removed students
        now = datetime.now(timezone.utc)
        for row in existing_rows:
            if getattr(row, "alumno_id") not in set(student_ids):
                row.estado = EstadoRegistro.INACTIVO  # type: ignore[attr-defined]
                row.deleted_at = now  # type: ignore[attr-defined]

        # Add new students
        for sid in student_ids:
            if sid not in existing_ids:
                instance = model_class(
                    tenant_id=self.tenant_id,
                    dictado_id=dictado_id,
                    alumno_id=sid,
                )
                self.session.add(instance)

        await self.session.flush()
        return len(student_ids)

    # ── Model stubs (replace with actual imports when C-04 exists) ──────

    @staticmethod
    def _get_actividad_model() -> Any:
        """Return the Actividad model (stub until C-04)."""
        from app.models.base import AppModel as _AppModel

        class _ActividadStub(_AppModel):
            __tablename__ = "actividades"
            __table_args__ = {"extend_existing": True}

        return _ActividadStub

    @staticmethod
    def _get_calificacion_model() -> Any:
        """Return the Calificacion model (stub until C-04)."""
        from app.models.base import AppModel as _AppModel

        class _CalificacionStub(_AppModel):
            __tablename__ = "calificaciones"
            __table_args__ = {"extend_existing": True}

        return _CalificacionStub

    @staticmethod
    def _get_alumno_dictado_model() -> Any:
        """Return the AlumnoDictado model (stub until C-04)."""
        from app.models.base import AppModel as _AppModel

        class _AlumnoDictadoStub(_AppModel):
            __tablename__ = "alumnos_dictados"
            __table_args__ = {"extend_existing": True}

        return _AlumnoDictadoStub
