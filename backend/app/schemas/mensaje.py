"""Pydantic schemas for the internal messaging system (C-13).

All schemas use ``extra='forbid'`` to reject undeclared fields (hard rule).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MensajeCreate(BaseModel):
    """Request schema for sending a new message.

    Attributes:
        destinatario_id: UUID of the recipient user.
        asunto: Message subject line (1-255 chars).
        cuerpo: Message body text.
    """

    model_config = ConfigDict(extra="forbid")

    destinatario_id: str = Field(
        ...,
        min_length=1,
        description="UUID of the recipient user",
    )
    asunto: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Message subject",
    )
    cuerpo: str = Field(
        ...,
        min_length=1,
        description="Message body text",
    )


class MensajeResponder(BaseModel):
    """Request schema for replying within a thread.

    Attributes:
        cuerpo: Reply body text.
    """

    model_config = ConfigDict(extra="forbid")

    cuerpo: str = Field(
        ...,
        min_length=1,
        description="Reply body text",
    )


class MensajeResponse(BaseModel):
    """Response schema for a single message."""

    model_config = ConfigDict(extra="forbid")

    id: str
    hilo_id: str
    remitente_id: str
    destinatario_id: str
    asunto: str
    cuerpo: str
    leido: bool
    created_at: datetime


class HiloResponse(BaseModel):
    """Response schema for a complete thread with all messages."""

    model_config = ConfigDict(extra="forbid")

    hilo_id: str
    asunto: str
    participantes: list[str]
    mensajes: list[MensajeResponse]


class InboxItemResponse(BaseModel):
    """Response schema for a single inbox item (thread summary)."""

    model_config = ConfigDict(extra="forbid")

    hilo_id: str
    asunto: str
    ultimo_mensaje: str
    ultima_fecha: datetime
    remitente_nombre: str
    no_leidos: int


class InboxResponse(BaseModel):
    """Response schema for the inbox listing."""

    model_config = ConfigDict(extra="forbid")

    data: list[InboxItemResponse]
    total: int
    limit: int
    offset: int


class MensajeCreatedResponse(BaseModel):
    """Response schema for a newly created message."""

    model_config = ConfigDict(extra="forbid")

    id: str
    hilo_id: str
    asunto: str
    created_at: datetime


class NoLeidosResponse(BaseModel):
    """Response schema for unread message count."""

    model_config = ConfigDict(extra="forbid")

    count: int
