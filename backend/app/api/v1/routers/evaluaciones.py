"""Router for Calendario Evaluaciones (F5.4 / HU-24).

Endpoints:
- GET  /api/evaluaciones                        — list with optional filters
- POST /api/evaluaciones                        — create
- PUT  /api/evaluaciones/{id}                   — partial update
- DELETE /api/evaluaciones/{id}                 — soft delete
- POST /api/materias/{materia_id}/evaluaciones/embed — LMS embed snippet

All endpoints are protected by ``require_permission("estructura_academica:gestionar")``.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
)

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.unit_of_work import UnitOfWork
from app.schemas.evaluaciones import (
    FechaEvaluacionCreate,
    FechaEvaluacionResponse,
    FechaEvaluacionUpdate,
)

router = APIRouter(tags=["evaluaciones"])


def _get_tenant_id(current_user: dict) -> str:
    """Extract tenant_id from the current user JWT payload."""
    return current_user.get("tenant_id", "")


# ── Helpers ──────────────────────────────────────────────────────────────────


def _build_embed_html(evaluaciones: list[FechaEvaluacionResponse]) -> str:
    """Build an HTML table snippet suitable for LMS embedding."""
    rows = ""
    for ev in evaluaciones:
        rows += (
            f"<tr>"
            f"<td>{ev.fecha.isoformat()}</td>"
            f"<td>{ev.tipo}</td>"
            f"<td>{ev.numero_instancia}</td>"
            f"<td>{_escape_html(ev.titulo)}</td>"
            f"</tr>\n"
        )
    return (
        '<table style="border-collapse:collapse;width:100%;font-family:sans-serif">\n'
        "  <thead>\n"
        "    <tr>"
        "<th>Fecha</th><th>Tipo</th><th>Inst.</th><th>Titulo</th>"
        "</tr>\n"
        "  </thead>\n"
        "  <tbody>\n"
        f"    {rows}"
        "  </tbody>\n"
        "</table>"
    )


def _build_embed_markdown(evaluaciones: list[FechaEvaluacionResponse]) -> str:
    """Build a Markdown table snippet suitable for LMS embedding."""
    lines = ["| Fecha | Tipo | Inst. | Titulo |", "|-------|------|-------|--------|"]
    for ev in evaluaciones:
        lines.append(
            f"| {ev.fecha.isoformat()} | {ev.tipo} | {ev.numero_instancia} | {_escape_md(ev.titulo)} |"
        )
    return "\n".join(lines) + "\n"


def _escape_html(text: str) -> str:
    """Escape special HTML characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_md(text: str) -> str:
    """Escape pipe characters in markdown table cells."""
    return text.replace("|", "\\|")


# ── List evaluations ─────────────────────────────────────────────────────────


@router.get(
    "/api/evaluaciones",
    status_code=HTTP_200_OK,
    response_model=list[FechaEvaluacionResponse],
)
async def list_evaluaciones(
    materia_id: str | None = Query(None),
    cohorte_id: str | None = Query(None),
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[FechaEvaluacionResponse]:
    """List evaluation dates with optional materia/cohorte filters (F5.4)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        items = await uow.evaluacion.list_by_filters(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
        )
        return [
            FechaEvaluacionResponse.model_validate(item)
            for item in items
        ]


# ── Create evaluation ────────────────────────────────────────────────────────


@router.post(
    "/api/evaluaciones",
    status_code=HTTP_201_CREATED,
    response_model=FechaEvaluacionResponse,
)
async def create_evaluacion(
    body: FechaEvaluacionCreate,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> FechaEvaluacionResponse:
    """Create a new evaluation date (F5.4)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        instance = await uow.evaluacion.create(body)
        await uow.evaluacion.session.flush()
        return FechaEvaluacionResponse.model_validate(instance)


# ── Update evaluation ────────────────────────────────────────────────────────


@router.put(
    "/api/evaluaciones/{id}",
    status_code=HTTP_200_OK,
    response_model=FechaEvaluacionResponse,
)
async def update_evaluacion(
    id: str,
    body: FechaEvaluacionUpdate,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> FechaEvaluacionResponse:
    """Partial update of an evaluation date (F5.4)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        instance = await uow.evaluacion.update(id, body)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Evaluacion not found",
            )
        return FechaEvaluacionResponse.model_validate(instance)


# ── Delete evaluation ────────────────────────────────────────────────────────


@router.delete(
    "/api/evaluaciones/{id}",
    status_code=HTTP_204_NO_CONTENT,
)
async def delete_evaluacion(
    id: str,
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> None:
    """Soft-delete an evaluation date (F5.4)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        await uow.evaluacion.soft_delete(id)


# ── Embed snippet ────────────────────────────────────────────────────────────


@router.post(
    "/api/materias/{materia_id}/evaluaciones/embed",
    status_code=HTTP_200_OK,
)
async def embed_evaluaciones(
    materia_id: str,
    formato: str = Query("html", pattern=r"^(html|markdown)$"),
    _: Annotated[None, Depends(require_permission("estructura_academica:gestionar"))] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    """Generate an embed snippet (HTML or Markdown) of upcoming evaluations for LMS (F5.4)."""
    async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
        items = await uow.evaluacion.list_by_filters(materia_id=materia_id)
        responses = [FechaEvaluacionResponse.model_validate(item) for item in items]

        if formato == "markdown":
            snippet = _build_embed_markdown(responses)
            content_type = "text/markdown"
        else:
            snippet = _build_embed_html(responses)
            content_type = "text/html"

        return {
            "formato": formato,
            "content_type": content_type,
            "total": len(responses),
            "snippet": snippet,
        }
