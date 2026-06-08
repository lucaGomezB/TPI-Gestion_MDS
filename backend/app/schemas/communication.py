"""Pydantic schemas for the communications queue (C-11).

All schemas use ``extra='forbid'`` per project convention.

Schemas:
- PreviewRequest, PreviewItem, PreviewResponse
- EnviarRequest, ComunicacionResponse, LoteResponse
- AprobarRequest, AprobarResponse
"""

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AccionAprobacion(str, enum.Enum):
    """Actions available for the approval decision (RN-17)."""

    aprobar = "aprobar"
    rechazar = "rechazar"


# ── Preview schemas (D-05) ────────────────────────────────────────────────


class PreviewRequest(BaseModel):
    """Request to preview rendered templates before sending (RN-16).

    Attributes:
        asunto: Template string for the email subject (may contain ``{{...}}``).
        cuerpo: Template string for the email body (may contain ``{{...}}``).
        alumno_ids: Optional list of specific alumno IDs to preview (max 5).
            If omitted, a random sample of up to 3 entries is used.
    """

    model_config = ConfigDict(extra="forbid")

    asunto: str = Field(..., min_length=1, max_length=500)
    cuerpo: str = Field(..., min_length=1)
    alumno_ids: Optional[list[str]] = Field(None, max_length=5)


class PreviewItem(BaseModel):
    """A single preview item for one recipient."""

    model_config = ConfigDict(extra="forbid")

    alumno_nombre: str
    email_preview: str
    asunto_renderizado: str
    cuerpo_renderizado: str


class PreviewResponse(BaseModel):
    """Response containing rendered previews for sample recipients."""

    model_config = ConfigDict(extra="forbid")

    previews: list[PreviewItem]


# ── Send schemas (D-05, D-06) ─────────────────────────────────────────────


class EnviarRequest(BaseModel):
    """Request to enqueue a bulk communication.

    Attributes:
        asunto: Template string for subject.
        cuerpo: Template string for body.
        preview_confirmado: MUST be True (RN-16 enforcement). If False or
            omitted, the service rejects the request.
        alumno_ids: Optional list of specific alumno IDs to send to.
            If omitted, send to all EntradaPadron entries for the materia.
    """

    model_config = ConfigDict(extra="forbid")

    asunto: str = Field(..., min_length=1, max_length=500)
    cuerpo: str = Field(..., min_length=1)
    preview_confirmado: bool = Field(...)
    alumno_ids: Optional[list[str]] = None


# ── Response schemas (D-13) ───────────────────────────────────────────────


class ComunicacionResponse(BaseModel):
    """Single communication record returned to the client.

    The ``destinatario`` field is masked for privacy (D-13).
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    materia_id: str
    destinatario: str
    asunto: str
    estado: str
    enviado_at: Optional[datetime] = None
    error_msg: Optional[str] = None


class LoteResponse(BaseModel):
    """Batch (Lote) summary returned for status tracking."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    materia_id: str
    total: int
    enviados: int
    fallidos: int
    estado: str
    requiere_aprobacion: bool
    created_at: datetime


# ── Approval schemas (RN-17) ──────────────────────────────────────────────


class AprobarRequest(BaseModel):
    """Request to approve or reject a bulk communication batch.

    Attributes:
        accion: ``aprobar`` to approve, ``rechazar`` to reject.
        motivo: Optional reason for the decision (required if rechazar).
    """

    model_config = ConfigDict(extra="forbid")

    accion: AccionAprobacion
    motivo: Optional[str] = Field(None, max_length=500)


class AprobarResponse(BaseModel):
    """Response after processing an approval decision."""

    model_config = ConfigDict(extra="forbid")

    id: str
    estado: str
    mensaje: str
