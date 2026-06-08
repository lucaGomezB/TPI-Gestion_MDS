"""Repository for Moodle sync persistence operations.

Handles upserting activities, grades, and enrollment data during sync
with proper tenant scoping and destructive replacement (RN-05) for
enrollment.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mixins import EstadoRegistro


class MoodleSyncRepository:
    """Repository for syncing Moodle data to internal models.

    Operates on raw dict DTOs and performs upsert logic.
    Actual model references are commented out until academic models (C-04)
    are available — this provides the contract for when they exist.
    """

    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def upsert_activities(
        self,
        dictado_id: str,
        activities: list[dict[str, Any]],
    ) -> int:
        """Upsert activities (grade items) for a dictado.

        Each activity dict must have at minimum:
        - ``moodle_item_id``: The Moodle grade item ID
        - ``nombre``: Activity name
        - ``tipo_escala``: 'numeric' or 'textual'

        Args:
            dictado_id: The internal dictado UUID.
            activities: List of activity DTOs.

        Returns:
            Number of activities upserted.
        """
        count = 0
        for act in activities:
            moodle_id = act.get("moodle_item_id")

            # Try to find existing activity by Moodle item ID
            # In C-04, this will query the Actividad model
            existing = await self.session.execute(
                select(self._get_actividad_model()).where(
                    self._get_actividad_model().tenant_id == self.tenant_id,  # type: ignore[union-attr]
                    self._get_actividad_model().dictado_id == dictado_id,  # type: ignore[union-attr]
                    self._get_actividad_model().moodle_item_id == moodle_id,  # type: ignore[union-attr]
                )
            )
            existing_row = existing.scalar_one_or_none()

            if existing_row:
                # Update existing
                for key, value in act.items():
                    if hasattr(existing_row, key):
                        setattr(existing_row, key, value)
                existing_row.updated_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
            else:
                # Create new - uses raw SQLAlchemy insert via the model
                model_class = self._get_actividad_model()
                new_act = model_class(
                    tenant_id=self.tenant_id,
                    dictado_id=dictado_id,
                    **{k: v for k, v in act.items() if k not in ("tenant_id", "dictado_id")},
                )
                self.session.add(new_act)

            count += 1

        await self.session.flush()
        return count

    async def upsert_grades(
        self,
        dictado_id: str,
        grades: list[dict[str, Any]],
    ) -> int:
        """Upsert grade records for students.

        Each grade dict must have:
        - ``actividad_id``: Internal activity UUID
        - ``alumno_id``: Internal alumno UUID
        - ``valor_numerico``: Numeric grade value (optional)
        - ``valor_textual``: Textual grade value (optional)

        Args:
            dictado_id: The internal dictado UUID.
            grades: List of grade DTOs.

        Returns:
            Number of grades upserted.
        """
        count = 0
        for grade in grades:
            actividad_id = grade.get("actividad_id")
            alumno_id = grade.get("alumno_id")

            existing = await self.session.execute(
                select(self._get_calificacion_model()).where(
                    self._get_calificacion_model().tenant_id == self.tenant_id,  # type: ignore[union-attr]
                    self._get_calificacion_model().actividad_id == actividad_id,  # type: ignore[union-attr]
                    self._get_calificacion_model().alumno_id == alumno_id,  # type: ignore[union-attr]
                )
            )
            existing_row = existing.scalar_one_or_none()

            if existing_row:
                for key, value in grade.items():
                    if hasattr(existing_row, key):
                        setattr(existing_row, key, value)
                existing_row.updated_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
            else:
                model_class = self._get_calificacion_model()
                new_grade = model_class(
                    tenant_id=self.tenant_id,
                    **grade,
                )
                self.session.add(new_grade)

            count += 1

        await self.session.flush()
        return count

    async def upsert_enrollment(
        self,
        dictado_id: str,
        student_ids: list[str],
    ) -> int:
        """Replace enrollment roster with destructive replacement (RN-05).

        Students in the new list are upserted. Students not in the new list
        are soft-deleted. This implements RN-05 destructive replacement.

        Args:
            dictado_id: The internal dictado UUID.
            student_ids: List of internal alumno UUIDs to enroll.

        Returns:
            Number of active enrollments after operation.
        """
        model_class = self._get_alumno_dictado_model()

        # Get existing enrollments
        existing_result = await self.session.execute(
            select(model_class).where(
                model_class.tenant_id == self.tenant_id,  # type: ignore[union-attr]
                model_class.dictado_id == dictado_id,  # type: ignore[union-attr]
                model_class.estado != EstadoRegistro.INACTIVO,  # type: ignore[union-attr]
            )
        )
        existing_rows = list(existing_result.scalars().all())
        existing_ids = {getattr(row, "alumno_id") for row in existing_rows}

        # Soft-delete students no longer in the roster
        now = datetime.now(timezone.utc)
        for row in existing_rows:
            alumno_id = getattr(row, "alumno_id")
            if alumno_id not in set(student_ids):
                row.estado = EstadoRegistro.INACTIVO  # type: ignore[attr-defined]
                row.deleted_at = now  # type: ignore[attr-defined]

        # Add new students not already enrolled
        for sid in student_ids:
            if sid not in existing_ids:
                new_enrollment = model_class(
                    tenant_id=self.tenant_id,
                    dictado_id=dictado_id,
                    alumno_id=sid,
                )
                self.session.add(new_enrollment)

        await self.session.flush()
        return len(student_ids)

    async def get_dictado_by_moodle_course(
        self,
        moodle_course_id: int,
    ) -> dict[str, Any] | None:
        """Find a dictado by its Moodle course ID.

        Args:
            moodle_course_id: The Moodle course ID.

        Returns:
            A dict with dictado data or None.
        """
        model_class = self._get_dictado_model()
        result = await self.session.execute(
            select(model_class).where(
                model_class.tenant_id == self.tenant_id,  # type: ignore[union-attr]
                model_class.moodle_course_id == moodle_course_id,  # type: ignore[union-attr]
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return {c.name: getattr(row, c.name) for c in row.__table__.columns}

    async def get_active_dictados_for_sync(
        self,
    ) -> list[dict[str, Any]]:
        """Get all active dictados with a moodle_course_id.

        Returns:
            A list of dictado dicts.
        """
        model_class = self._get_dictado_model()
        result = await self.session.execute(
            select(model_class).where(
                model_class.tenant_id == self.tenant_id,  # type: ignore[union-attr]
                model_class.moodle_course_id.isnot(None),  # type: ignore[union-attr]
                model_class.estado != EstadoRegistro.INACTIVO,  # type: ignore[union-attr]
            )
        )
        rows = result.scalars().all()
        return [
            {c.name: getattr(r, c.name) for c in r.__table__.columns}
            for r in rows
        ]

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

    @staticmethod
    def _get_dictado_model() -> Any:
        """Return the Dictado model (stub until C-04)."""
        from app.models.base import AppModel as _AppModel

        class _DictadoStub(_AppModel):
            __tablename__ = "dictados"
            __table_args__ = {"extend_existing": True}

        return _DictadoStub
