"""Admin router for reportes endpoints (monitor general).

Endpoints:
- GET /api/admin/monitor/actividades — cross-subject activity monitoring (F2.7)

Permissions:
- ``reportes:monitor_general`` for monitor (COORDINADOR + ADMIN only)

Scope:
- Tenant-wide cross-subject data.
- COORDINADOR and ADMIN only. PROFESOR and TUTOR get 403.
"""

import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.reportes import MonitorGeneralResponse
from app.services.reportes_monitor import ReportesMonitorService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin", "reportes"])


# ── GET /api/admin/monitor/actividades (F2.7) ─────────────────────────────────


@router.get(
    "/api/admin/materias/monitor-general",
    response_model=MonitorGeneralResponse,
)
async def monitor_actividades(
    _: Annotated[None, Depends(require_permission("reportes:monitor_general"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    materia_id: Annotated[
        str | None, Query(description="Filter by materia ID")
    ] = None,
    regional: Annotated[
        str | None, Query(description="Filter by regional")
    ] = None,
    comision: Annotated[
        str | None, Query(description="Filter by comision")
    ] = None,
    estado_actividad: Annotated[
        str | None, Query(description="Filter by 'pendiente' or 'completo'")
    ] = None,
    busqueda: Annotated[
        str | None, Query(description="Search by nombre or apellidos")
    ] = None,
    fecha_desde: Annotated[
        date | None, Query(description="Filter grades from date")
    ] = None,
    fecha_hasta: Annotated[
        date | None, Query(description="Filter grades until date")
    ] = None,
) -> MonitorGeneralResponse:
    """Get cross-subject activity monitoring for the tenant (F2.7).

    Only available for COORDINADOR and ADMIN roles.
    Provides consolidated activity status across all subjects with filters.

    Args:
        current_user: Authenticated user from JWT.
        db: Database session.
        materia_id: Optional filter by materia.
        regional: Optional filter by student regional.
        comision: Optional filter by comision.
        estado_actividad: Optional filter by "pendiente" or "completo".
        busqueda: Optional search by student name.
        fecha_desde: Optional date range start.
        fecha_hasta: Optional date range end.

    Returns:
        A ``MonitorGeneralResponse`` with items and aggregate metrics.
    """
    tenant_id = current_user.get("tenant_id", "")

    async with UnitOfWork(db, tenant_id) as uow:
        service = ReportesMonitorService(uow)
        result = await service.get_monitor_general(
            materia_id=materia_id,
            regional=regional,
            comision=comision,
            estado_actividad=estado_actividad,
            busqueda=busqueda,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        # Audit log
        await service._log_audit_monitor(
            actor_id=current_user.get("id", ""),
        )

        return result


@router.get(
    "/api/admin/materias/monitor-general/export",
)
async def export_monitor_general(
    _: Annotated[None, Depends(require_permission("reportes:monitor_general"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    materia_id: Annotated[
        str | None, Query(description="Filter by materia ID")
    ] = None,
    regional: Annotated[
        str | None, Query(description="Filter by regional")
    ] = None,
    comision: Annotated[
        str | None, Query(description="Filter by comision")
    ] = None,
    busqueda: Annotated[
        str | None, Query(description="Search by nombre or apellidos")
    ] = None,
    status: Annotated[
        str | None, Query(description="Filter: todos, con_atrasados, sin_datos")
    ] = None,
) -> StreamingResponse:
    """Export monitor general data as CSV.

    Returns a StreamingResponse with Content-Type text/csv for browser download.
    """
    import csv
    import io
    from fastapi.responses import StreamingResponse

    tenant_id = current_user.get("tenant_id", "")

    async with UnitOfWork(db, tenant_id) as uow:
        service = ReportesMonitorService(uow)
        result = await service.get_monitor_general(
            materia_id=materia_id,
            regional=regional,
            comision=comision,
            busqueda=busqueda,
            estado_actividad=status,
        )

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "materia_id", "materia_nombre", "cohorte", "comision",
                "total_alumnos", "total_actividades", "promedio_general",
                "aprobados", "reprobados", "atrasados_count", "pendientes_count",
            ],
        )
        writer.writeheader()
        for item in result.items:
            writer.writerow(item.model_dump())

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=monitor-general.csv"},
        )
