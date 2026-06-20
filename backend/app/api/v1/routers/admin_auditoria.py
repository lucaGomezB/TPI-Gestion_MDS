"""Admin router for audit log — search, export, and docente interaction panel.

Endpoints:
- ``GET /api/admin/auditoria`` — full-text search with filters, paginated
- ``GET /api/admin/auditoria/exportar`` — export search results as CSV/JSON
- ``GET /api/admin/auditoria/docentes/{docente_id}/interacciones`` — aggregated
  interaction metrics per teacher (F9.1)

All endpoints are protected by ``require_permission("auditoria:ver")``.
The ``tenant_id`` is resolved from the JWT (never from request params).
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.audit import (
    AuditExportParams,
    AuditLogSearchParams,
    AuditLogSearchResponse,
    DocenteInteraccionesResponse,
)
from app.services.audit_service import AuditService

router = APIRouter(tags=["admin", "auditoria"])


@router.get(
    "/api/admin/auditoria",
    response_model=AuditLogSearchResponse,
)
async def search_audit_log(
    params: Annotated[AuditLogSearchParams, Depends()],
    current_user: Annotated[dict, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission("auditoria:ver"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuditLogSearchResponse:
    """Search the audit log with full-text query and filters.

    All results are scoped to the caller's tenant (from JWT).
    Pagination is applied via ``limit`` (default 50, max 200) and ``offset``.

    Returns a paginated response with ``items``, ``total``, ``limit``, ``offset``.
    """
    async with UnitOfWork(db, current_user["tenant_id"]) as uow:
        service = AuditService(uow)
        return await service.search(
            tenant_id=current_user["tenant_id"],
            q=params.q,
            accion=params.accion,
            actor_id=params.actor_id,
            materia_id=params.materia_id,
            ip=params.ip,
            fecha_desde=params.fecha_desde,
            fecha_hasta=params.fecha_hasta,
            limit=params.limit,
            offset=params.offset,
        )


@router.get(
    "/api/admin/auditoria/exportar",
)
async def export_audit_log(
    params: Annotated[AuditExportParams, Depends()],
    current_user: Annotated[dict, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission("auditoria:ver"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    """Export audit log search results as CSV or JSON.

    Accepts the same filter parameters as the search endpoint plus
    ``formato`` (``csv`` | ``json``, default ``csv``).

    Returns a ``StreamingResponse`` with appropriate Content-Type and
    Content-Disposition headers for download.
    """
    async with UnitOfWork(db, current_user["tenant_id"]) as uow:
        service = AuditService(uow)
        return await service.export(
            tenant_id=current_user["tenant_id"],
            q=params.q,
            accion=params.accion,
            actor_id=params.actor_id,
            materia_id=params.materia_id,
            ip=params.ip,
            fecha_desde=params.fecha_desde,
            fecha_hasta=params.fecha_hasta,
            formato=params.formato,
        )


@router.get(
    "/api/admin/auditoria/docentes/{docente_id}/interacciones",
    response_model=DocenteInteraccionesResponse,
)
async def get_docente_interacciones(
    docente_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission("auditoria:ver"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocenteInteraccionesResponse:
    """Get aggregated interaction metrics for a teacher (F9.1).

    Returns total actions, breakdown by action code and by materia,
    and the 200 most recent actions — all scoped to the caller's tenant.
    """
    async with UnitOfWork(db, current_user["tenant_id"]) as uow:
        service = AuditService(uow)
        return await service.get_docente_interacciones(
            tenant_id=current_user["tenant_id"],
            docente_id=docente_id,
        )


@router.get(
    "/api/admin/auditoria/acciones-por-dia",
)
async def get_acciones_por_dia(
    fecha_desde: str,
    fecha_hasta: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission("auditoria:ver"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """Get daily action counts for the audit dashboard chart.

    Returns a list of ``{fecha: str, total: int}`` for each day in the range.
    """
    from datetime import date

    from sqlalchemy import func, select

    from app.models.audit_log import AuditLog

    tenant_id = current_user["tenant_id"]
    desde = date.fromisoformat(fecha_desde)
    hasta = date.fromisoformat(fecha_hasta)

    async with db.begin():
        result = await db.execute(
            select(
                func.date(AuditLog.fecha_hora).label("fecha"),
                func.count().label("total"),
            )
            .where(
                AuditLog.tenant_id == tenant_id,
                func.date(AuditLog.fecha_hora) >= desde,
                func.date(AuditLog.fecha_hora) <= hasta,
            )
            .group_by(func.date(AuditLog.fecha_hora))
            .order_by(func.date(AuditLog.fecha_hora))
        )
        rows = result.all()

    return [{"fecha": str(r.fecha), "total": r.total} for r in rows]
