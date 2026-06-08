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
    MonitorEntryOut,
    MonitorGeneralResponse,
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
    ) -> MonitorGeneralResponse:
        """Get cross-subject activity status for all students.

        Args:
            materia_id: Optional filter by materia.
            regional: Optional filter by student regional.
            comision: Optional filter by comision.
            estado_actividad: Optional filter by "pendiente" or "completo".
            busqueda: Optional ILIKE search on nombre/apellidos.
            fecha_desde: Optional date range start.
            fecha_hasta: Optional date range end.

        Returns:
            A ``MonitorGeneralResponse`` with items and aggregate metrics.
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

        metrics = await self.repo.get_metricas_generales()

        items = [
            MonitorEntryOut(
                entrada_padron_id=item["entrada_padron_id"],
                nombre=item["nombre"],
                apellidos=item["apellidos"],
                comision=item.get("comision"),
                regional=item.get("regional"),
                materia_nombre=item["materia_nombre"],
                materia_id=item["materia_id"],
                total_actividades=item["total_actividades"],
                total_aprobadas=item["total_aprobadas"],
                total_pendientes=item["total_pendientes"],
                ultima_actividad=item.get("ultima_actividad"),
            )
            for item in items_data
        ]

        return MonitorGeneralResponse(
            items=items,
            total=len(items),
            total_alumnos=metrics["total_alumnos"],
            total_materias=metrics["total_materias"],
            total_actividades=metrics["total_actividades"],
            total_aprobadas=metrics["total_aprobadas"],
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
