"""Service layer for export-atrasados operations (F2.6).

Provides:
- ``detectar_sin_corregir``: Heuristic detection of uncorrected TPs (RN-07/RN-08).
- ``export_csv``: Build downloadable CSV from export-atrasados data.

Design (per C-10 design.md):
- D2: Uses heuristic based on available Calificacion data (F1.2 not yet available).
- D5: CSV export via shared ``_build_csv_rows`` utility.
"""

from datetime import date
from typing import Any

from app.core.action_codes import AccionAuditoria
from app.core.unit_of_work import UnitOfWork
from app.schemas.reportes import (
    ExportAtrasadoEntryOut,
    ExportAtrasadosResponse,
)
from app.services.audit_service import AuditService
from app.services.reportes_notas import _build_csv_rows


# ── Pure functions (testable without database) ────────────────────────────────


def _detectar_sin_corregir(
    alumnos: list[dict],
    actividades_textuales: list[str],
) -> list[dict]:
    """Detect students potentially missing textual grades (RN-07 heuristic).

    RN-07: Cross-reference LMS completion data with imported grades.
    RN-08: Only textual activities are considered.

    Since F1.2 (LMS completion import) is not yet available, the heuristic
    identifies students who are in the active padron but lack a textual
    Calificacion record for activities where textual grades exist for
    other students.

    Args:
        alumnos: List of student dicts with ``calificaciones`` list.
        actividades_textuales: List of textual activity names to check.

    Returns:
        A list of dicts with keys: nombre, apellidos, comision, actividad,
        estado.
    """
    if not actividades_textuales:
        return []

    sin_corregir: list[dict] = []
    for alumno in alumnos:
        graded_activities = {
            c["actividad"]
            for c in alumno.get("calificaciones", [])
            if c.get("nota_textual") is not None
        }

        for actividad in actividades_textuales:
            if actividad not in graded_activities:
                sin_corregir.append({
                    "entrada_padron_id": alumno["entrada_padron_id"],
                    "nombre": alumno["nombre"],
                    "apellidos": alumno["apellidos"],
                    "comision": alumno.get("comision"),
                    "actividad": actividad,
                    "estado": "sin_corregir",
                })

    return sin_corregir


# ── ReportesExportService ────────────────────────────────────────────────────


class ReportesExportService:
    """Business logic for export-atrasados operations.

    Args:
        uow: The ``UnitOfWork`` instance for data access.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.tenant_id = uow._tenant_id or ""
        self.repo = uow.reportes_export

    async def detectar_sin_corregir(
        self,
        materia_id: str,
        comision: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> ExportAtrasadosResponse:
        """Detect potentially uncorrected TPs for a materia (RN-07/RN-08).

        Args:
            materia_id: The materia UUID.
            comision: Optional filter by comision.
            fecha_desde: Optional date range start.
            fecha_hasta: Optional date range end.

        Returns:
            An ``ExportAtrasadosResponse`` with items and total count.
        """
        # Step 1: Get textual activities (RN-08 filter)
        actividades_textuales = await self.repo.get_actividades_textuales(
            materia_id=materia_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        if not actividades_textuales:
            return ExportAtrasadosResponse(items=[], total=0)

        # Step 2: Get students without textual grades for these activities
        alumnos = await self.repo.get_alumnos_sin_calificacion_textual(
            materia_id=materia_id,
            actividades_textuales=actividades_textuales,
            comision=comision,
        )

        # Step 3: Apply heuristic detection
        sin_corregir = _detectar_sin_corregir(
            alumnos, actividades_textuales
        )

        items = [
            ExportAtrasadoEntryOut(
                nombre=item["nombre"],
                apellidos=item["apellidos"],
                comision=item.get("comision"),
                actividad=item["actividad"],
                estado=item["estado"],
            )
            for item in sin_corregir
        ]

        return ExportAtrasadosResponse(
            items=items,
            total=len(items),
        )

    def export_csv(
        self,
        data: list[dict],
    ) -> str:
        """Build CSV string from export-atrasados data.

        Args:
            data: List of dicts with export atrasado entry data.

        Returns:
            A CSV string with UTF-8 BOM.
        """
        headers = [
            "nombre", "apellidos", "comision",
            "actividad", "estado",
        ]
        return _build_csv_rows(headers, data)

    async def _log_audit(
        self,
        actor_id: str,
        materia_id: str,
    ) -> None:
        """Log an audit entry for export-atrasados query.

        Args:
            actor_id: The user's UUID.
            materia_id: The materia UUID.
        """
        audit_service = AuditService(self.uow)
        await audit_service.log_action(
            accion=AccionAuditoria.EXPORT_ATRASADOS_CONSULTAR,
            actor_id=actor_id,
            tenant_id=self.tenant_id,
            materia_id=materia_id,
        )
