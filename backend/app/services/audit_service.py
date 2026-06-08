"""Audit service — log actions, search, export, and docente interaction panel.

Services call ``log_action()`` explicitly after completing significant
write operations (calificaciones import, padron upload, comunicacion send,
etc.). The service validates the action code against ``AccionAuditoria``
and delegates persistence to ``AuditRepository``.
"""

import csv
import io
from datetime import datetime
from typing import Any

from fastapi.responses import StreamingResponse

from app.core.action_codes import AccionAuditoria
from app.core.unit_of_work import UnitOfWork
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogSearchResponse,
    DocenteInteraccionesResponse,
)


class AuditService:
    """Business logic for audit log operations.

    Args:
        uow: The ``UnitOfWork`` instance for data access.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ── Log an action (core audit operation) ────────────────────────────────

    async def log_action(
        self,
        accion: AccionAuditoria | str,
        actor_id: str,
        tenant_id: str,
        materia_id: str | None = None,
        impersonado_id: str | None = None,
        detalle: dict[str, Any] | None = None,
        filas_afectadas: int | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLogResponse:
        """Create an immutable audit log entry.

        Args:
            accion: The action code — must be a valid ``AccionAuditoria`` member.
            actor_id: UUID of the user who performed the action.
            tenant_id: UUID of the tenant.
            materia_id: Optional UUID of the subject context.
            impersonado_id: Optional UUID of the impersonated user.
            detalle: Optional arbitrary JSON-serializable context.
                MUST NOT contain PII (email, DNI, CUIL, CBU, alias CBU).
            filas_afectadas: Optional count of records affected.
            ip: Optional client IP address.
            user_agent: Optional HTTP User-Agent header.

        Returns:
            An ``AuditLogResponse`` with the created entry.

        Raises:
            ValueError: If ``accion`` is not a valid ``AccionAuditoria`` member.
        """
        # Validate action code
        if isinstance(accion, AccionAuditoria):
            accion_str = accion.value
        elif isinstance(accion, str):
            try:
                accion_str = AccionAuditoria(accion).value
            except ValueError:
                msg = (
                    f"Invalid action code: '{accion}'. "
                    f"Must be one of {[e.value for e in AccionAuditoria]}"
                )
                raise ValueError(msg) from None
        else:
            msg = (
                f"Invalid action code type: {type(accion).__name__}. "
                f"Must be AccionAuditoria or str."
            )
            raise ValueError(msg)

        data = {
            "accion": accion_str,
            "actor_id": actor_id,
            "tenant_id": tenant_id,
            "materia_id": materia_id,
            "impersonado_id": impersonado_id,
            "detalle": detalle,
            "filas_afectadas": filas_afectadas,
            "ip": ip,
            "user_agent": user_agent,
        }

        entry = await self.uow.audit.create(data)
        return AuditLogResponse.model_validate(entry)

    # ── Search ──────────────────────────────────────────────────────────────

    async def search(
        self,
        tenant_id: str,
        q: str | None = None,
        accion: str | None = None,
        actor_id: str | None = None,
        materia_id: str | None = None,
        ip: str | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLogSearchResponse:
        """Full-text search with filters.

        Args:
            Same as ``AuditRepository.search()``.

        Returns:
            An ``AuditLogSearchResponse`` with items, total, limit, offset.
        """
        items, total = await self.uow.audit.search(
            tenant_id=tenant_id,
            q=q,
            accion=accion,
            actor_id=actor_id,
            materia_id=materia_id,
            ip=ip,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limit=limit,
            offset=offset,
        )
        return AuditLogSearchResponse(
            items=[AuditLogResponse.model_validate(e) for e in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    # ── Docente interacciones ───────────────────────────────────────────────

    async def get_docente_interacciones(
        self, tenant_id: str, docente_id: str
    ) -> DocenteInteraccionesResponse:
        """Get aggregated interaction metrics for a teacher (F9.1).

        Args:
            tenant_id: Required — scopes results to the caller's tenant.
            docente_id: The teacher's UUID.

        Returns:
            A ``DocenteInteraccionesResponse`` with aggregated metrics.
        """
        data = await self.uow.audit.get_docente_interacciones(
            tenant_id=tenant_id,
            docente_id=docente_id,
        )
        return DocenteInteraccionesResponse(
            docente_id=data["docente_id"],
            total_acciones=data["total_acciones"],
            por_accion=data["por_accion"],
            por_materia=data["por_materia"],
            ultimas_acciones=[
                AuditLogResponse.model_validate(e)
                for e in data["ultimas_acciones"]
            ],
        )

    # ── Export ──────────────────────────────────────────────────────────────

    async def export(
        self,
        tenant_id: str,
        q: str | None = None,
        accion: str | None = None,
        actor_id: str | None = None,
        materia_id: str | None = None,
        ip: str | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        formato: str = "csv",
    ) -> StreamingResponse:
        """Export search results as CSV or JSON.

        Args:
            Same filter parameters as ``search()``.
            formato: ``"csv"`` (default) or ``"json"``.

        Returns:
            A ``StreamingResponse`` with appropriate Content-Type and
            Content-Disposition headers.
        """
        rows = await self.uow.audit.export_search(
            tenant_id=tenant_id,
            q=q,
            accion=accion,
            actor_id=actor_id,
            materia_id=materia_id,
            ip=ip,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if formato == "json":
            import json

            json_bytes = json.dumps(rows, default=str, ensure_ascii=False).encode(
                "utf-8"
            )
            return StreamingResponse(
                iter([json_bytes]),
                media_type="application/json",
                headers={
                    "Content-Disposition": (
                        f'attachment; filename="auditoria-export-{timestamp}.json"'
                    ),
                },
            )

        # CSV export
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        else:
            output.write("id,tenant_id,fecha_hora,actor_id,impersonado_id,materia_id,")
            output.write("accion,detalle,filas_afectadas,ip,user_agent\n")

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue().encode("utf-8")]),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="auditoria-export-{timestamp}.csv"'
                ),
            },
        )
