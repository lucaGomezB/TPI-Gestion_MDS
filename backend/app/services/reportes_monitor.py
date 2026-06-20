"""Service layer for monitor and seguimiento operations (F2.7-F2.9).

Provides:
- ``get_monitor_general``: Cross-subject activity monitoring for COORDINADOR/ADMIN.
- ``get_seguimiento``: Per-subject student monitoring with role-aware scope.

Design (per C-10 design.md):
- D3: Repository returns raw data; service formats response.
- D4: Role-aware scope in seguimiento (TUTOR/PROFESOR vs COORDINADOR/ADMIN).
"""

from datetime import date
from typing import Any

from app.core.action_codes import AccionAuditoria
from app.core.unit_of_work import UnitOfWork
from app.schemas.reportes import (
    MonitorGeneralAggregatedResponse,
    MonitorGeneralItemOut,
    SeguimientoActividadOut,
    SeguimientoEntryOut,
    SeguimientoResponse,
)
from app.services.audit_service import AuditService
from app.services.reportes_notas import _calcular_promedio_cumplimiento


# ── ReportesMonitorService ───────────────────────────────────────────────────


class ReportesMonitorService:
    """Business logic for monitor and seguimiento operations.

    Args:
        uow: The ``UnitOfWork`` instance for data access.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.tenant_id = uow._tenant_id or ""
        self.repo = uow.reportes_monitor

    # ── Monitor General (F2.7) ──────────────────────────────────────────

    async def get_monitor_general(
        self,
        materia_id: str | None = None,
        regional: str | None = None,
        comision: str | None = None,
        estado_actividad: str | None = None,
        busqueda: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        status: str | None = None,
    ) -> MonitorGeneralAggregatedResponse:
        """Get cross-subject activity status aggregated by materia+cohorte+comision.

        Args:
            materia_id: Optional filter by materia.
            regional: Optional filter by student regional.
            comision: Optional filter by comision.
            estado_actividad: Optional filter by "pendiente" or "completo".
            busqueda: Optional ILIKE search on nombre/apellidos.
            fecha_desde: Optional date range start.
            fecha_hasta: Optional date range end.
            status: Optional filter: "con_atrasados" or "sin_datos".

        Returns:
            A ``MonitorGeneralAggregatedResponse`` with items and aggregate metrics.
        """
        items_data = await self.repo.get_monitor_general(
            materia_id=materia_id,
            regional=regional,
            comision=comision,
            estado_actividad=estado_actividad,
            busqueda=busqueda,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        # Aggregate per-student data into per-materia+cohorte+comision groups
        from collections import defaultdict

        groups: dict[tuple, list[dict]] = defaultdict(list)
        for item in items_data:
            key = (
                item["materia_id"],
                item["materia_nombre"],
                item.get("cohorte_nombre", ""),
                item.get("comision") or "",
            )
            groups[key].append(item)

        aggregated: list[MonitorGeneralItemOut] = []
        for (mat_id, mat_nombre, cohorte, com), students in groups.items():
            unique_students = set(s["entrada_padron_id"] for s in students)
            total_alumnos = len(unique_students)
            total_actividades = sum(s["total_actividades"] for s in students)
            total_pendientes_sum = sum(s["total_pendientes"] for s in students)

            # Students with 0 pendientes = aprobados (completely caught up)
            aprobados = sum(1 for s in students if s["total_pendientes"] == 0)
            reprobados = total_alumnos - aprobados

            # Average approval ratio across students
            ratios = [
                s["total_aprobadas"] / s["total_actividades"]
                if s["total_actividades"] > 0
                else 0.0
                for s in students
            ]
            promedio_general = round(
                sum(ratios) / len(ratios) if ratios else 0.0,
                2,
            )

            aggregated.append(
                MonitorGeneralItemOut(
                    materia_id=mat_id,
                    materia_nombre=mat_nombre,
                    cohorte=cohorte,
                    comision=com if com else None,
                    total_alumnos=total_alumnos,
                    total_actividades=total_actividades,
                    promedio_general=promedio_general,
                    aprobados=aprobados,
                    reprobados=reprobados,
                    atrasados_count=reprobados,
                    pendientes_count=total_pendientes_sum,
                )
            )

        # Apply status filter at the aggregated level
        if status == "con_atrasados":
            aggregated = [a for a in aggregated if a.atrasados_count > 0]
        elif status == "sin_datos":
            aggregated = [a for a in aggregated if a.total_actividades == 0]

        return MonitorGeneralAggregatedResponse(
            items=aggregated,
            total=len(aggregated),
        )

    # ── Seguimiento (F2.8, F2.9) ───────────────────────────────────────

    async def get_seguimiento(
        self,
        materia_id: str,
        cargado_por: str | None = None,
        comision: str | None = None,
        regional: str | None = None,
        actividad: str | None = None,
        minimo_actividades_cumplidas: int | None = None,
        busqueda: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> SeguimientoResponse:
        """Get per-student seguimiento data for a materia.

        Args:
            materia_id: The materia UUID.
            cargado_por: If set (PROFESOR), scope to this user's grades.
            comision: Optional filter by comision.
            regional: Optional filter by regional.
            actividad: Optional filter by activity name.
            minimo_actividades_cumplidas: Min approved activities.
            busqueda: Optional ILIKE search on nombre/apellidos.
            fecha_desde: Optional date range start.
            fecha_hasta: Optional date range end.

        Returns:
            A ``SeguimientoResponse`` with items and aggregate metrics.
        """
        alumnos = await self.repo.get_seguimiento(
            materia_id=materia_id,
            cargado_por=cargado_por,
            comision=comision,
            regional=regional,
            actividad=actividad,
            minimo_actividades_cumplidas=minimo_actividades_cumplidas,
            busqueda=busqueda,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        items: list[SeguimientoEntryOut] = []
        for alumno in alumnos:
            total_actividades = alumno["total_actividades"]
            total_aprobadas = alumno["total_aprobadas"]
            porcentaje_cumplimiento = round(
                (total_aprobadas / total_actividades * 100)
                if total_actividades > 0 else 0.0,
                2,
            )

            actividades = [
                SeguimientoActividadOut(
                    actividad_nombre=c["actividad"],
                    nota_numerica=c.get("nota_numerica"),
                    nota_textual=c.get("nota_textual"),
                    aprobado=c["aprobado"],
                )
                for c in alumno["calificaciones"]
            ]

            items.append(SeguimientoEntryOut(
                entrada_padron_id=alumno["entrada_padron_id"],
                nombre=alumno["nombre"],
                apellidos=alumno["apellidos"],
                comision=alumno.get("comision"),
                actividades=actividades,
                total_actividades=total_actividades,
                total_aprobadas=total_aprobadas,
                porcentaje_cumplimiento=porcentaje_cumplimiento,
            ))

        total_alumnos = len(alumnos)
        promedio_cumplimiento = _calcular_promedio_cumplimiento(
            [{"porcentaje_cumplimiento": i.porcentaje_cumplimiento} for i in items]
        )

        return SeguimientoResponse(
            items=items,
            total=len(items),
            total_alumnos=total_alumnos,
            promedio_cumplimiento=promedio_cumplimiento,
        )

    # ── Audit logging ──────────────────────────────────────────────────

    async def _log_audit_monitor(
        self,
        actor_id: str,
    ) -> None:
        """Log an audit entry for monitor general query.

        Args:
            actor_id: The user's UUID.
        """
        audit_service = AuditService(self.uow)
        await audit_service.log_action(
            accion=AccionAuditoria.MONITOR_GENERAL_CONSULTAR,
            actor_id=actor_id,
            tenant_id=self.tenant_id,
        )

    async def _log_audit_seguimiento(
        self,
        actor_id: str,
        materia_id: str,
    ) -> None:
        """Log an audit entry for seguimiento query.

        Args:
            actor_id: The user's UUID.
            materia_id: The materia UUID.
        """
        audit_service = AuditService(self.uow)
        await audit_service.log_action(
            accion=AccionAuditoria.SEGUIMIENTO_CONSULTAR,
            actor_id=actor_id,
            tenant_id=self.tenant_id,
            materia_id=materia_id,
        )
