"""Router for atrasados, ranking, and reportes endpoints.

Endpoints:
- GET /api/materias/{materia_id}/atrasados — list at-risk students
- GET /api/materias/{materia_id}/ranking — ranking by approved activities
- GET /api/materias/{materia_id}/reportes — consolidated metrics

All endpoints support ``?exportar=csv`` for CSV download.

Permissions:
- ``atrasados:ver`` for atrasados and ranking (PROFESOR + higher)
- ``reportes:ver`` for reportes (PROFESOR + higher)
- ``calificaciones:exportar`` for CSV export (PROFESOR + COORDINADOR)

Scope (RN-08):
- PROFESOR: only sees data for grades they imported.
- COORDINADOR/ADMIN: sees all data for the materia.
"""

import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
)

from app.core.action_codes import AccionAuditoria
from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.models.asignacion import Asignacion
from app.schemas.atrasados_ranking import (
    AtrasadosListResponse,
    RankingListResponse,
    ReportesOut,
)
from app.services.atrasados_ranking import AtrasadosRankingService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["atrasados-ranking"])


# ── Shared helpers (D8: reuse pattern from calificaciones router) ──────────


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
    PROFESOR must have an active assignment for the materia.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        The asignacion UUID if the user is a PROFESOR with assignment,
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


# ── GET /atrasados ───────────────────────────────────────────────────────────


@router.get(
    "/api/materias/{materia_id}/atrasados",
    response_model=AtrasadosListResponse,
)
async def listar_atrasados(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("atrasados:ver"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    comision: Annotated[str | None, Query(description="Filter by comision")] = None,
    busqueda: Annotated[
        str | None, Query(description="Search by nombre or apellidos")
    ] = None,
    fecha_desde: Annotated[
        date | None, Query(description="Filter grades from date")
    ] = None,
    fecha_hasta: Annotated[
        date | None, Query(description="Filter grades until date")
    ] = None,
    exportar: Annotated[
        str | None, Query(description="Set to 'csv' for CSV export")
    ] = None,
) -> AtrasadosListResponse | StreamingResponse:
    """List at-risk students for a materia (RN-06).

    Supports optional filters and CSV export via ``?exportar=csv``.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.
        comision: Optional filter by comision.
        busqueda: Optional search by student name.
        fecha_desde: Optional date range start.
        fecha_hasta: Optional date range end.
        exportar: If 'csv', returns CSV instead of JSON.

    Returns:
        ``AtrasadosListResponse`` or ``StreamingResponse`` for CSV.
    """
    await _check_materia_access(materia_id, current_user, db)

    es_coordinador = _is_coordinador(current_user)
    cargado_por = None if es_coordinador else current_user.get("id")

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AtrasadosRankingService(uow)
        result = await service.list_atrasados(
            materia_id=materia_id,
            cargado_por=cargado_por,
            comision=comision,
            busqueda=busqueda,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        # Audit log
        await service._log_audit(
            accion=AccionAuditoria.ATRASADOS_CONSULTAR,
            actor_id=current_user.get("id", ""),
            materia_id=materia_id,
        )

        # CSV export
        if exportar and exportar.lower() == "csv":
            # Build raw data for CSV from the response items
            csv_data = [
                {
                    "nombre": item.nombre,
                    "apellidos": item.apellidos,
                    "email": item.email,
                    "comision": item.comision or "",
                    "razon": item.razon,
                    "nota_minima": str(item.nota_minima) if item.nota_minima is not None else "",
                    "umbral": str(item.umbral) if item.umbral is not None else "",
                    "total_actividades": item.total_actividades,
                }
                for item in result.items
            ]
            csv_content = service.export_csv(
                csv_data, "atrasados", materia_id
            )
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


# ── GET /ranking ─────────────────────────────────────────────────────────────


@router.get(
    "/api/materias/{materia_id}/ranking",
    response_model=RankingListResponse,
)
async def obtener_ranking(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("atrasados:ver"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    comision: Annotated[str | None, Query(description="Filter by comision")] = None,
    busqueda: Annotated[
        str | None, Query(description="Search by nombre or apellidos")
    ] = None,
    exportar: Annotated[
        str | None, Query(description="Set to 'csv' for CSV export")
    ] = None,
) -> RankingListResponse | StreamingResponse:
    """Get ranking of students by approved activities (RN-09).

    Only students with >= 1 approved activity are included.
    Supports CSV export via ``?exportar=csv``.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.
        comision: Optional filter by comision.
        busqueda: Optional search by student name.
        exportar: If 'csv', returns CSV instead of JSON.

    Returns:
        ``RankingListResponse`` or ``StreamingResponse`` for CSV.
    """
    await _check_materia_access(materia_id, current_user, db)

    es_coordinador = _is_coordinador(current_user)
    cargado_por = None if es_coordinador else current_user.get("id")

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AtrasadosRankingService(uow)
        result = await service.get_ranking(
            materia_id=materia_id,
            cargado_por=cargado_por,
            comision=comision,
            busqueda=busqueda,
        )

        # Audit log
        await service._log_audit(
            accion=AccionAuditoria.RANKING_CONSULTAR,
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
                    "total_aprobadas": item.total_aprobadas,
                    "total_actividades": item.total_actividades,
                    "porcentaje_aprobacion": item.porcentaje_aprobacion,
                }
                for item in result.items
            ]
            csv_content = service.export_csv(
                csv_data, "ranking", materia_id
            )
            return StreamingResponse(
                iter([csv_content.encode("utf-8")]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": (
                        f'attachment; filename="ranking-{materia_id}.csv"'
                    ),
                },
            )

        return result


# ── GET /reportes ────────────────────────────────────────────────────────────


@router.get(
    "/api/materias/{materia_id}/reportes",
    response_model=ReportesOut,
)
async def obtener_reportes(
    materia_id: str,
    _: Annotated[None, Depends(require_permission("reportes:ver"))],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportesOut:
    """Get consolidated subject metrics.

    Args:
        materia_id: The materia UUID.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        A ``ReportesOut`` with computed metrics.
    """
    await _check_materia_access(materia_id, current_user, db)

    es_coordinador = _is_coordinador(current_user)
    cargado_por = None if es_coordinador else current_user.get("id")

    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        service = AtrasadosRankingService(uow)
        result = await service.get_reportes(
            materia_id=materia_id,
            cargado_por=cargado_por,
        )

        # Audit log
        await service._log_audit(
            accion=AccionAuditoria.ATRASADOS_CONSULTAR,
            actor_id=current_user.get("id", ""),
            materia_id=materia_id,
        )

        return result
