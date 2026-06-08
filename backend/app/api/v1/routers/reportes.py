"""Router for reportes endpoints (notas-finales, export-atrasados, seguimiento).

Endpoints:
- GET /api/materias/{materia_id}/notas-finales — final grades per student (F2.5)
- GET /api/materias/{materia_id}/export/atrasados — uncorrected TPs (F2.6)
- GET /api/materias/{materia_id}/seguimiento — per-subject monitoring (F2.8, F2.9)

Permissions:
- ``reportes:notas_finales`` for notas-finales (PROFESOR + higher)
- ``reportes:exportar_atrasados`` for export-atrasados (PROFESOR + COORDINADOR)
- ``reportes:seguimiento`` for seguimiento (TUTOR, PROFESOR + higher)

Scope:
- PROFESOR/TUTOR: only sees data scoped to their assignments.
- COORDINADOR/ADMIN: sees all data for the materia.
"""

import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.models.asignacion import Asignacion
from app.schemas.reportes import (
    ExportAtrasadosResponse,
    NotasFinalesResponse,
    SeguimientoResponse,
)
from app.services.reportes_export import ReportesExportService
from app.services.reportes_monitor import ReportesMonitorService
from app.services.reportes_notas import ReportesNotasService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reportes"])


# ── Shared helpers ────────────────────────────────────────────────────────────


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


async def _check_materia_access(
    materia_id: str,
    current_user: dict,
    db: AsyncSession,
) -> str | None:
    """Check materia access and return asignacion_id if applicable.

    COORDINADOR and ADMIN roles can access any materia within the tenant.
    PROFESOR/TUTOR must have an active assignment for the materia.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        The asignacion UUID if the user has a specific assignment,
        or None if COORDINADOR/ADMIN.

    Raises:
        HTTPException(403): If the user does not have access.
    """
    roles = current_user.get("roles", [])
    user_id = current_user.get("id", "")

    if "COORDINADOR" in roles or "ADMIN" in roles:
        return None

    today = date.today()
    stmt = (
        select(Asignacion)
        .where(
            Asignacion.tenant_id == _get_tenant_id(current_user),
            Asignacion.usuario_id == user_id,
            Asignacion.materia_id == materia_id,
            Asignacion.vig_desde <= today,
            (
                (Asignacion.vig_hasta >= today)
                | (Asignacion.vig_hasta.is_(None))
            ),
        )
    )
    result = await db.execute(stmt)
    asignacion = result.scalar_one_or_none()
    if asignacion is None:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta materia",
        )
    return asignacion.id


def _is_coordinador(current_user: dict) -> bool:
    """Check if the current user has COORDINADOR or ADMIN role."""
    roles = current_user.get("roles", [])
    return "COORDINADOR" in roles or "ADMIN" in roles


# ── GET /materias/{materia_id}/notas-finales (F2.5) ───────────────────────────


@router.get(
    "/api/materias/{materia_id}/notas-finales",
    response_model=NotasFinalesResponse,
)
async def listar_notas_finales(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("reportes:notas_finales"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    comision: Annotated[str | None, Query(description="Filter by comision")] = None,
    busqueda: Annotated[
        str | None, Query(description="Search by nombre or apellidos")
    ] = None,
    exportar: Annotated[
        str | None, Query(description="Set to 'csv' for CSV export")
    ] = None,
) -> NotasFinalesResponse | StreamingResponse:
    """List final grades per student for a materia (F2.5).

    Supports optional filters and CSV export via ``?exportar=csv``.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.
        comision: Optional filter by comision.
        busqueda: Optional search by student name.
        exportar: If 'csv', returns CSV instead of JSON.

    Returns:
        ``NotasFinalesResponse`` or ``StreamingResponse`` for CSV.
    """
    await _check_materia_access(materia_id, current_user, db)

    es_coordinador = _is_coordinador(current_user)
    cargado_por = None if es_coordinador else current_user.get("id")

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ReportesNotasService(uow)
        result = await service.get_notas_finales(
            materia_id=materia_id,
            cargado_por=cargado_por,
            comision=comision,
            busqueda=busqueda,
        )

        # Audit log
        await service._log_audit(
            actor_id=current_user.get("id", ""),
            materia_id=materia_id,
        )

        # CSV export
        if exportar and exportar.lower() == "csv":
            csv_data = [
                {
                    "nombre": item.nombre,
                    "apellidos": item.apellidos,
                    "comision": item.comision or "",
                    "total_actividades": str(item.total_actividades),
                    "nota_final": f"{item.nota_final:.2f}",
                    "estado": item.estado,
                }
                for item in result.items
            ]
            csv_content = service.export_csv(csv_data)
            return StreamingResponse(
                iter([csv_content.encode("utf-8")]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": (
                        f'attachment; filename="notas-finales-{materia_id}.csv"'
                    ),
                },
            )

        return result


# ── GET /materias/{materia_id}/export/atrasados (F2.6) ────────────────────────


@router.get(
    "/api/materias/{materia_id}/export/atrasados",
    response_model=ExportAtrasadosResponse,
)
async def exportar_atrasados(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("reportes:exportar_atrasados"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    comision: Annotated[str | None, Query(description="Filter by comision")] = None,
    fecha_desde: Annotated[
        date | None, Query(description="Filter grades from date")
    ] = None,
    fecha_hasta: Annotated[
        date | None, Query(description="Filter grades until date")
    ] = None,
    exportar: Annotated[
        str | None, Query(description="Set to 'csv' for CSV export")
    ] = None,
) -> ExportAtrasadosResponse | StreamingResponse:
    """Export uncorrected TPs for a materia (F2.6, RN-07/RN-08).

    Detects students without textual grades for activities where textual
    grades exist. Only textual activities are considered (RN-08).

    Supports optional filters and CSV export via ``?exportar=csv``.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.
        comision: Optional filter by comision.
        fecha_desde: Optional date range start.
        fecha_hasta: Optional date range end.
        exportar: If 'csv', returns CSV instead of JSON.

    Returns:
        ``ExportAtrasadosResponse`` or ``StreamingResponse`` for CSV.
    """
    await _check_materia_access(materia_id, current_user, db)

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ReportesExportService(uow)
        result = await service.detectar_sin_corregir(
            materia_id=materia_id,
            comision=comision,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        # Audit log
        await service._log_audit(
            actor_id=current_user.get("id", ""),
            materia_id=materia_id,
        )

        # CSV export
        if exportar and exportar.lower() == "csv":
            csv_data = [
                {
                    "nombre": item.nombre,
                    "apellidos": item.apellidos,
                    "comision": item.comision or "",
                    "actividad": item.actividad,
                    "estado": item.estado,
                }
                for item in result.items
            ]
            csv_content = service.export_csv(csv_data)
            return StreamingResponse(
                iter([csv_content.encode("utf-8")]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": (
                        f'attachment; filename="atrasados-{materia_id}.csv"'
                    ),
                },
            )

        return result


# ── GET /materias/{materia_id}/seguimiento (F2.8, F2.9) ───────────────────────


@router.get(
    "/api/materias/{materia_id}/seguimiento",
    response_model=SeguimientoResponse,
)
async def obtener_seguimiento(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("reportes:seguimiento"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    actividad: Annotated[
        str | None, Query(description="Filter by activity name")
    ] = None,
    comision: Annotated[str | None, Query(description="Filter by comision")] = None,
    regional: Annotated[
        str | None, Query(description="Filter by regional")
    ] = None,
    minimo_actividades_cumplidas: Annotated[
        int | None, Query(description="Min approved activities")
    ] = None,
    busqueda: Annotated[
        str | None, Query(description="Search by nombre or apellidos")
    ] = None,
    fecha_desde: Annotated[
        date | None, Query(description="Filter grades from date (COORDINADOR/ADMIN)")
    ] = None,
    fecha_hasta: Annotated[
        date | None, Query(description="Filter grades until date (COORDINADOR/ADMIN)")
    ] = None,
) -> SeguimientoResponse:
    """Get per-subject student monitoring (F2.8 for TUTOR/PROFESOR, F2.9 for COORDINADOR/ADMIN).

    Role-aware behavior:
    - TUTOR/PROFESOR: scope limited to their assigned comisiones or grades.
    - COORDINADOR/ADMIN: all students in the materia, with date range filters.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.
        actividad: Optional filter by activity name.
        comision: Optional filter by comision.
        regional: Optional filter by regional.
        minimo_actividades_cumplidas: Min approved activities (HAVING).
        busqueda: Optional search by student name.
        fecha_desde: Optional date range start (COORDINADOR/ADMIN only).
        fecha_hasta: Optional date range end (COORDINADOR/ADMIN only).

    Returns:
        A ``SeguimientoResponse`` with items and aggregate metrics.
    """
    await _check_materia_access(materia_id, current_user, db)

    es_coordinador = _is_coordinador(current_user)
    cargado_por = None if es_coordinador else current_user.get("id")

    # Only COORDINADOR/ADMIN can use date range filters
    if not es_coordinador and (fecha_desde is not None or fecha_hasta is not None):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Solo coordinadores y administradores pueden usar filtros de fecha",
        )

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = ReportesMonitorService(uow)
        result = await service.get_seguimiento(
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

        # Audit log
        await service._log_audit_seguimiento(
            actor_id=current_user.get("id", ""),
            materia_id=materia_id,
        )

        return result
