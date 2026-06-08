"""Service layer for atrasados, ranking, and reportes operations.

Provides:
- ``list_atrasados``: Detect at-risk students using RN-06 logic.
- ``get_ranking``: Rank students by approved activities (RN-09).
- ``get_reportes``: Consolidated subject metrics.
- ``export_csv``: Build downloadable CSV from data.

Design (per C-09 design.md):
- D2: Repository returns raw data; pure functions in this module apply
      RN-06 logic to classify atrasados.
- D3: Ranking uses COUNT + HAVING from repository; service only formats.
- Pure functions are extracted for testability without database.
"""

import csv
import io
from datetime import date
from typing import Any

from app.core.action_codes import AccionAuditoria
from app.core.unit_of_work import UnitOfWork
from app.schemas.atrasados_ranking import (
    ActividadMetricaOut,
    AlumnoAtrasadoOut,
    AtrasadosListResponse,
    MetricsOut,
    RankingEntryOut,
    RankingListResponse,
    ReportesOut,
)
from app.services.audit_service import AuditService


# ── Pure functions (testable without database) ────────────────────────────────


def _clasificar_alumnos(
    alumnos: list[dict], umbral: int = 60
) -> list[dict]:
    """Classify students as atrasados using RN-06 logic.

    RN-06: A student is atrasado if:
    - They have NO grades (faltante).
    - OR their lowest numeric grade is below the configured threshold (nota_baja).

    Args:
        alumnos: List of student dicts with ``calificaciones`` list.
        umbral: The approval threshold percentage.

    Returns:
        A list of atrasado student dicts with keys: nombre, apellidos, email,
        comision, razon, nota_minima, umbral, total_actividades.
    """
    atrasados: list[dict] = []
    for alumno in alumnos:
        calificaciones = alumno.get("calificaciones", [])
        total_actividades = len(calificaciones)

        if total_actividades == 0:
            atrasados.append({
                "nombre": alumno["nombre"],
                "apellidos": alumno["apellidos"],
                "email": alumno["email"],
                "comision": alumno.get("comision"),
                "razon": "faltante",
                "nota_minima": None,
                "umbral": umbral,
                "total_actividades": 0,
            })
            continue

        # Find minimum numeric grade
        notas_numericas = [
            c["nota_numerica"]
            for c in calificaciones
            if c["nota_numerica"] is not None
        ]

        if notas_numericas:
            nota_minima = min(notas_numericas)
            if nota_minima < umbral:
                atrasados.append({
                    "nombre": alumno["nombre"],
                    "apellidos": alumno["apellidos"],
                    "email": alumno["email"],
                    "comision": alumno.get("comision"),
                    "razon": "nota_baja",
                    "nota_minima": nota_minima,
                    "umbral": umbral,
                    "total_actividades": total_actividades,
                })
        # If no numeric grades but has textual grades, not atrasado by RN-06

    return atrasados


def _ordenar_ranking(ranking_data: list[dict]) -> list[dict]:
    """Sort ranking data by total_aprobadas descending (RN-09).

    Args:
        ranking_data: List of ranking dicts from repository.

    Returns:
        Sorted list of dicts.
    """
    return sorted(
        ranking_data,
        key=lambda r: r["total_aprobadas"],
        reverse=True,
    )


def _calculate_porcentaje(aprobadas: int, total: int) -> float:
    """Calculate percentage with 2 decimal rounding.

    Args:
        aprobadas: Number of approved activities.
        total: Total number of activities.

    Returns:
        Percentage rounded to 2 decimal places, or 0.0 if total is 0.
    """
    if total == 0:
        return 0.0
    return round((aprobadas / total) * 100, 2)


# ── CSV export ───────────────────────────────────────────────────────────────


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


# ── AtrasadosRankingService ──────────────────────────────────────────────────


class AtrasadosRankingService:
    """Business logic for atrasados, ranking, and reportes operations.

    Args:
        uow: The ``UnitOfWork`` instance for data access.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.tenant_id = uow._tenant_id or ""
        self.repo = uow.atrasados_ranking

    # ── List atrasados (RN-06) ──────────────────────────────────────────

    async def list_atrasados(
        self,
        materia_id: str,
        cargado_por: str | None = None,
        comision: str | None = None,
        busqueda: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> AtrasadosListResponse:
        """List at-risk students for a materia (RN-06).

        Args:
            materia_id: The materia UUID.
            cargado_por: If set (PROFESOR), scope to this user's grades.
            comision: Optional filter by comision name.
            busqueda: Optional ILIKE search on nombre/apellidos.
            fecha_desde: Optional date range start.
            fecha_hasta: Optional date range end.

        Returns:
            An ``AtrasadosListResponse`` with items and metrics.
        """
        alumnos = await self.repo.get_alumnos_con_calificaciones(
            materia_id=materia_id,
            cargado_por=cargado_por,
            comision=comision,
            busqueda=busqueda,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        total_alumnos = len(alumnos)
        atrasados = _clasificar_alumnos(alumnos)

        items = [
            AlumnoAtrasadoOut(
                nombre=a["nombre"],
                apellidos=a["apellidos"],
                email=a["email"],
                comision=a.get("comision"),
                razon=a["razon"],
                nota_minima=a.get("nota_minima"),
                umbral=a.get("umbral"),
                total_actividades=a["total_actividades"],
            )
            for a in atrasados
        ]

        return AtrasadosListResponse(
            items=items,
            total=len(items),
            metrics=MetricsOut(
                total_alumnos=total_alumnos,
                total_atrasados=len(items),
            ),
        )

    # ── Get ranking (RN-09) ─────────────────────────────────────────────

    async def get_ranking(
        self,
        materia_id: str,
        cargado_por: str | None = None,
        comision: str | None = None,
        busqueda: str | None = None,
    ) -> RankingListResponse:
        """Get ranking of students by approved activities (RN-09).

        Only students with >= 1 approved activity are included.

        Args:
            materia_id: The materia UUID.
            cargado_por: If set (PROFESOR), scope to this user's grades.
            comision: Optional filter by comision name.
            busqueda: Optional ILIKE search on nombre/apellidos.

        Returns:
            A ``RankingListResponse`` with items sorted by approved count.
        """
        ranking_data = await self.repo.get_ranking(
            materia_id=materia_id,
            cargado_por=cargado_por,
            comision=comision,
            busqueda=busqueda,
        )

        sorted_data = _ordenar_ranking(ranking_data)

        items = [
            RankingEntryOut(
                nombre=r["nombre"],
                apellidos=r["apellidos"],
                comision=r.get("comision"),
                total_aprobadas=r["total_aprobadas"],
                total_actividades=r["total_actividades"],
                porcentaje_aprobacion=_calculate_porcentaje(
                    r["total_aprobadas"], r["total_actividades"]
                ),
            )
            for r in sorted_data
        ]

        return RankingListResponse(
            items=items,
            total=len(items),
        )

    # ── Get reportes ───────────────────────────────────────────────────

    async def get_reportes(
        self,
        materia_id: str,
        cargado_por: str | None = None,
    ) -> ReportesOut:
        """Get consolidated subject metrics.

        Args:
            materia_id: The materia UUID.
            cargado_por: If set (PROFESOR), scope to this user's data.

        Returns:
            A ``ReportesOut`` with calculated metrics.
        """
        metrics = await self.repo.get_metricas(
            materia_id=materia_id,
            cargado_por=cargado_por,
        )

        total_alumnos = metrics["total_alumnos"]
        total_atrasados: int = 0

        # Calculate atrasados count from the alumnos data
        if total_alumnos > 0:
            alumnos = await self.repo.get_alumnos_con_calificaciones(
                materia_id=materia_id,
                cargado_por=cargado_por,
            )
            atrasados = _clasificar_alumnos(alumnos)
            total_atrasados = len(atrasados)

        actividades = [
            ActividadMetricaOut(
                nombre=a["nombre"],
                total_alumnos=a["total_alumnos"],
                total_aprobados=a["total_aprobados"],
            )
            for a in metrics["actividades"]
        ]

        return ReportesOut(
            total_alumnos=total_alumnos,
            alumnos_con_calificaciones=metrics["alumnos_con_calificaciones"],
            total_atrasados=total_atrasados,
            total_aprobadas=metrics["total_aprobadas"],
            total_calificaciones=metrics["total_calificaciones"],
            actividades=actividades,
            porcentaje_atrasados=_calculate_porcentaje(
                total_atrasados, total_alumnos
            ),
        )

    # ── Export CSV ─────────────────────────────────────────────────────

    def export_csv(
        self,
        data: list[dict],
        endpoint_type: str,
        materia_id: str,
    ) -> str:
        """Build CSV string from atrasados or ranking data.

        Args:
            data: List of dicts to export (from list_atrasados or get_ranking).
            endpoint_type: ``"atrasados"`` or ``"ranking"``.
            materia_id: The materia UUID (used in filename).

        Returns:
            A CSV string with UTF-8 BOM.
        """
        if endpoint_type == "atrasados":
            headers = [
                "nombre", "apellidos", "email", "comision",
                "razon", "nota_minima", "umbral", "total_actividades",
            ]
        elif endpoint_type == "ranking":
            headers = [
                "nombre", "apellidos", "comision",
                "total_aprobadas", "total_actividades", "porcentaje_aprobacion",
            ]
        else:
            raise ValueError(f"Unknown endpoint_type: {endpoint_type}")

        return _build_csv_rows(headers, data)

    # ── Audit logging helper ──────────────────────────────────────────

    async def _log_audit(
        self,
        accion: AccionAuditoria,
        actor_id: str,
        materia_id: str,
    ) -> None:
        """Log an audit entry for a query action.

        Args:
            accion: The audit action code.
            actor_id: The user's UUID.
            materia_id: The materia UUID.
        """
        audit_service = AuditService(self.uow)
        await audit_service.log_action(
            accion=accion,
            actor_id=actor_id,
            tenant_id=self.tenant_id,
            materia_id=materia_id,
        )
