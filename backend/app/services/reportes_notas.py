"""Service layer for notas-finales operations (F2.5).

Provides:
- ``calcular_nota_final``: Compute final grade per student.
- ``export_csv``: Build downloadable CSV from notas-finales data.

Design (per C-10 design.md):
- D1: Note calculation happens in service, not SQL.
- D5: CSV export via shared ``_build_csv_rows`` utility.
"""

import csv
import io
from typing import Any

from app.core.action_codes import AccionAuditoria
from app.core.unit_of_work import UnitOfWork
from app.schemas.reportes import (
    NotaFinalEntryOut,
    NotasFinalesResponse,
)
from app.services.audit_service import AuditService


# ── Pure functions (testable without database) ────────────────────────────────


def _calcular_nota_final(
    calificaciones: list[dict],
    umbral_pct: int = 60,
) -> dict:
    """Calculate final grade for a student from their calificaciones.

    The final grade is the average of all numeric grades. Textual grades
    do NOT affect the numeric average but ARE counted in total_actividades.
    The estado is "aprobado" if the numeric average >= umbral_pct.

    Args:
        calificaciones: List of calificacion dicts with ``nota_numerica``,
            ``nota_textual``, ``aprobado`` keys.
        umbral_pct: The approval threshold percentage (default 60).

    Returns:
        A dict with ``nota_final``, ``estado``, ``total_actividades``.
    """
    total_actividades = len(calificaciones)
    notas_numericas = [
        c["nota_numerica"]
        for c in calificaciones
        if c["nota_numerica"] is not None
    ]

    if not notas_numericas:
        nota_final = 0.0
        estado = "reprobado"
    else:
        nota_final = round(sum(notas_numericas) / len(notas_numericas), 2)
        estado = "aprobado" if nota_final >= umbral_pct else "reprobado"

    return {
        "nota_final": nota_final,
        "estado": estado,
        "total_actividades": total_actividades,
    }


def _build_csv_rows(headers: list[str], data: list[dict]) -> str:
    """Build a CSV string from data.

    Uses UTF-8 BOM and semicolon delimiter for Excel compatibility on Windows.

    Args:
        headers: Ordered list of column header names.
        data: List of dicts with the data.

    Returns:
        A CSV string with BOM prefix.
    """
    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM
    writer = csv.DictWriter(output, fieldnames=headers, delimiter=";")
    writer.writeheader()
    for row in data:
        writer.writerow({
            h: row.get(h, "") for h in headers
        })
    return output.getvalue()


def _calcular_promedio_cumplimiento(items: list[dict]) -> float:
    """Calculate average cumplimiento percentage from items.

    Args:
        items: List of dicts with ``porcentaje_cumplimiento`` key.

    Returns:
        Average rounded to 2 decimal places, or 0.0 if empty.
    """
    if not items:
        return 0.0
    total = sum(item["porcentaje_cumplimiento"] for item in items)
    return round(total / len(items), 2)


# ── ReportesNotasService ─────────────────────────────────────────────────────


class ReportesNotasService:
    """Business logic for notas-finales operations.

    Args:
        uow: The ``UnitOfWork`` instance for data access.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.tenant_id = uow._tenant_id or ""
        self.repo = uow.reportes_notas

    async def get_notas_finales(
        self,
        materia_id: str,
        cargado_por: str | None = None,
        comision: str | None = None,
        busqueda: str | None = None,
        umbral_pct: int = 60,
    ) -> NotasFinalesResponse:
        """Get final grades for all students in a materia.

        Args:
            materia_id: The materia UUID.
            cargado_por: If set (PROFESOR), scope to this user's grades.
            comision: Optional filter by comision.
            busqueda: Optional ILIKE search on nombre/apellidos.
            umbral_pct: Approval threshold percentage.

        Returns:
            A ``NotasFinalesResponse`` with items and metrics.
        """
        alumnos = await self.repo.get_calificaciones_agrupadas(
            materia_id=materia_id,
            cargado_por=cargado_por,
            comision=comision,
            busqueda=busqueda,
        )

        items: list[NotaFinalEntryOut] = []
        for alumno in alumnos:
            resultado = _calcular_nota_final(
                alumno["calificaciones"], umbral_pct
            )
            items.append(NotaFinalEntryOut(
                entrada_padron_id=alumno["entrada_padron_id"],
                nombre=alumno["nombre"],
                apellidos=alumno["apellidos"],
                comision=alumno.get("comision"),
                total_actividades=resultado["total_actividades"],
                nota_final=resultado["nota_final"],
                estado=resultado["estado"],
            ))

        total_alumnos = len(alumnos)
        notas = [i.nota_final for i in items if i.total_actividades > 0]
        promedio_general = round(sum(notas) / len(notas), 2) if notas else 0.0

        return NotasFinalesResponse(
            items=items,
            total=len(items),
            total_alumnos=total_alumnos,
            promedio_general=promedio_general,
        )

    def export_csv(
        self,
        data: list[dict],
    ) -> str:
        """Build CSV string from notas-finales data.

        Args:
            data: List of dicts with nota final entry data.

        Returns:
            A CSV string with UTF-8 BOM.
        """
        headers = [
            "nombre", "apellidos", "comision",
            "total_actividades", "nota_final", "estado",
        ]
        return _build_csv_rows(headers, data)

    async def _log_audit(
        self,
        actor_id: str,
        materia_id: str,
    ) -> None:
        """Log an audit entry for notas-finales query.

        Args:
            actor_id: The user's UUID.
            materia_id: The materia UUID.
        """
        audit_service = AuditService(self.uow)
        await audit_service.log_action(
            accion=AccionAuditoria.NOTAS_FINALES_CONSULTAR,
            actor_id=actor_id,
            tenant_id=self.tenant_id,
            materia_id=materia_id,
        )
