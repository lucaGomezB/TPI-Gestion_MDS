"""Sync engine service — orchestrates Moodle WS → domain mapping → persistence.

Divides the sync pipeline into independent steps with granular error handling.
Each step has its own try/except block, enabling partial success reporting.
"""

import logging
from typing import Any

from app.core.unit_of_work import UnitOfWork
from app.integrations.exceptions import MoodleAuthenticationError, MoodleConnectionError
from app.integrations.moodle_ws import MoodleWSClient
from app.repositories.moodle_sync_repository import MoodleSyncRepository
from app.repositories.sync_log_repository import SyncLogRepository
from app.schemas.moodle_config import MoodleConfigSchema
from app.schemas.moodle_sync import SyncResult, SyncStep

logger = logging.getLogger(__name__)


class MoodleSyncService:
    """Orchestrates the full Moodle sync pipeline.

    Sync steps:
    1. Fetch grade items (activity catalog)
    2. Fetch enrolled users (enrollment roster)
    3. Fetch grades (per-student grades)
    4. Persist activities (upsert)
    5. Persist enrollment (destructive replacement per RN-05)
    6. Persist grades (upsert)
    """

    def __init__(self) -> None:
        self._sync_log_repo: SyncLogRepository | None = None
        self._sync_repo: MoodleSyncRepository | None = None

    async def sync_dictado(
        self,
        uow: UnitOfWork,
        tenant_id: str,
        dictado_id: str,
        moodle_course_id: int,
        moodle_config: MoodleConfigSchema,
        sync_type: str = "ondemand",
    ) -> SyncResult:
        """Execute the full sync pipeline for a dictado.

        Args:
            uow: The ``UnitOfWork`` instance for data access.
            tenant_id: The tenant UUID.
            dictado_id: The internal dictado UUID.
            moodle_course_id: The Moodle course ID to sync from.
            moodle_config: The decrypted Moodle configuration.
            sync_type: 'ondemand', 'nocturnal', or 'manual_import'.

        Returns:
            A ``SyncResult`` with status and counts.
        """
        # Initialize repos
        self._sync_log_repo = uow.sync_log
        self._sync_repo = uow.moodle_sync

        # Create sync log entry
        sync_log = await self._sync_log_repo.create(
            sync_type=sync_type,
            status="running",
            dictado_id=dictado_id,
        )

        steps: list[SyncStep] = []
        errors: list[str] = []
        activities_synced = 0
        students_synced = 0
        grade_items_synced = 0

        # Create Moodle WS client
        client = MoodleWSClient(
            ws_url=moodle_config.ws_url or "",
            ws_token=moodle_config.ws_token or "",
        )

        try:
            # ── Step 1: Fetch grade items ───────────────────────────────
            step1 = SyncStep(name="fetch_grade_items", status="running")
            try:
                grade_items = await client.get_grade_items(moodle_course_id)
                step1.status = "completed"
                step1.records_affected = len(grade_items)
                logger.info(
                    "Step 1: Fetched %d grade items for course %d",
                    len(grade_items),
                    moodle_course_id,
                )
            except Exception as exc:
                step1.status = "failed"
                step1.error = str(exc)
                errors.append(f"fetch_grade_items: {exc}")
                logger.error("Step 1 failed: %s", exc)
            steps.append(step1)

            # ── Step 2: Fetch enrolled users ────────────────────────────
            step2 = SyncStep(name="fetch_enrolled_users", status="running")
            try:
                enrolled_users = await client.get_enrolled_users(moodle_course_id)
                step2.status = "completed"
                step2.records_affected = len(enrolled_users)
                logger.info(
                    "Step 2: Fetched %d enrolled users for course %d",
                    len(enrolled_users),
                    moodle_course_id,
                )
            except Exception as exc:
                enrolled_users = []
                step2.status = "failed"
                step2.error = str(exc)
                errors.append(f"fetch_enrolled_users: {exc}")
                logger.error("Step 2 failed: %s", exc)
            steps.append(step2)

            # ── Step 3: Fetch grades ─────────────────────────────────────
            step3 = SyncStep(name="fetch_grades", status="running")
            try:
                grades_response = await client.get_grades(moodle_course_id)
                step3.status = "completed"
                step3.records_affected = len(grades_response.grades)
                logger.info(
                    "Step 3: Fetched %d grades for course %d",
                    len(grades_response.grades),
                    moodle_course_id,
                )
            except Exception as exc:
                grades_response = None
                step3.status = "failed"
                step3.error = str(exc)
                errors.append(f"fetch_grades: {exc}")
                logger.error("Step 3 failed: %s", exc)
            steps.append(step3)

            # ── Step 4: Persist activities ──────────────────────────────
            step4 = SyncStep(name="persist_activities", status="running")
            if step1.status == "completed":
                try:
                    activity_dtos = [
                        {
                            "moodle_item_id": item.id,
                            "nombre": item.itemname or f"Activity {item.id}",
                            "tipo_escala": "numeric" if item.scaleid is None else "textual",
                            "puntaje_maximo": item.grademax,
                        }
                        for item in grade_items
                    ]
                    count = await self._sync_repo.upsert_activities(
                        dictado_id=dictado_id,
                        activities=activity_dtos,
                    )
                    step4.status = "completed"
                    step4.records_affected = count
                    activities_synced = count
                except Exception as exc:
                    step4.status = "failed"
                    step4.error = str(exc)
                    errors.append(f"persist_activities: {exc}")
                    logger.error("Step 4 failed: %s", exc)
            else:
                step4.status = "skipped"
                step4.error = "Step 1 failed, no activities to persist"
            steps.append(step4)

            # ── Step 5: Persist enrollment ──────────────────────────────
            step5 = SyncStep(name="persist_enrollment", status="running")
            if step2.status == "completed" and enrolled_users:
                try:
                    # Map Moodle users to internal alumno IDs
                    student_ids = [
                        _map_user_to_student_id(u.id)
                        for u in enrolled_users
                    ]
                    count = await self._sync_repo.upsert_enrollment(
                        dictado_id=dictado_id,
                        student_ids=student_ids,
                    )
                    step5.status = "completed"
                    step5.records_affected = count
                    students_synced = count
                except Exception as exc:
                    step5.status = "failed"
                    step5.error = str(exc)
                    errors.append(f"persist_enrollment: {exc}")
                    logger.error("Step 5 failed: %s", exc)
            else:
                step5.status = "skipped"
                if not enrolled_users:
                    step5.error = "No enrolled users to persist"
                else:
                    step5.error = "Step 2 failed, no enrollment data"
            steps.append(step5)

            # ── Step 6: Persist grades ──────────────────────────────────
            step6 = SyncStep(name="persist_grades", status="running")
            if step3.status == "completed" and grades_response:
                try:
                    grade_dtos = [
                        {
                            "moodle_user_id": g.userid,
                            "moodle_item_id": gi.id,
                            "valor_numerico": g.rawgrade,
                            "valor_textual": g.grade if g.rawgrade is None else None,
                        }
                        for gi in (grades_response.grade_items or [])
                        for g in (grades_response.grades or [])
                        if g.rawgrade is not None or g.grade is not None
                    ]
                    count = await self._sync_repo.upsert_grades(
                        dictado_id=dictado_id,
                        grades=grade_dtos,
                    )
                    step6.status = "completed"
                    step6.records_affected = count
                    grade_items_synced = count
                except Exception as exc:
                    step6.status = "failed"
                    step6.error = str(exc)
                    errors.append(f"persist_grades: {exc}")
                    logger.error("Step 6 failed: %s", exc)
            else:
                step6.status = "skipped"
                step6.error = "Step 3 failed, no grades to persist"
            steps.append(step6)

        except (MoodleAuthenticationError, MoodleConnectionError) as exc:
            # Critical errors that prevent all steps
            errors.append(f"moodle_connection: {exc}")
            logger.error("Moodle connection error during sync: %s", exc)

        finally:
            await client.close()

        # Determine overall status
        step_statuses = {s.status for s in steps}
        if all(s == "completed" for s in step_statuses if s != "skipped"):
            overall_status = "completed"
        elif any(s == "completed" for s in step_statuses):
            overall_status = "partial"
        else:
            overall_status = "failed"

        # Update sync log
        await self._sync_log_repo.update_status(
            log_id=sync_log.id,
            status=overall_status,
            error_message="; ".join(errors) if errors else None,
            details={
                "steps": [s.model_dump() for s in steps],
                "moodle_course_id": moodle_course_id,
                "sync_type": sync_type,
            },
        )

        return SyncResult(
            status=overall_status,
            sync_log_id=sync_log.id,
            activities_synced=activities_synced,
            students_synced=students_synced,
            grade_items_synced=grade_items_synced,
            errors=errors,
        )


def _map_user_to_student_id(moodle_user_id: int) -> str:
    """Map a Moodle user ID to an internal student UUID.

    For MVP, this uses a deterministic UUID v5 based on the Moodle user ID.
    When C-04 (user profile sync) is implemented, this will query the
    actual alumno_id from the internal user mapping.

    Args:
        moodle_user_id: The Moodle user numeric ID.

    Returns:
        A deterministic UUID string.
    """
    import uuid

    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"moodle-user-{moodle_user_id}"))


moodle_sync_service = MoodleSyncService()
