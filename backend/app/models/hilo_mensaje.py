"""HiloMensaje model — message thread grouping.

A thread represents a conversation between two or more users on a specific
subject. Participants are stored as a JSONB array of user UUID strings.

Per Decision 1 from design.md: HiloMensaje is a separate entity (not inferred
from asunto) to allow explicit thread lifecycle management.

Per Decision 2: Participants are stored as JSONB array (simpler than a join
table for the current 1:1 use case, migratable to join table if 3+ needed).
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TimestampMixin


class HiloMensaje(AppModel, TimestampMixin):
    """A message thread grouping messages by subject.

    Attributes:
        id: UUID primary key.
        tenant_id: Tenant scope (non-nullable FK).
        asunto: Thread subject line.
        participantes: JSONB array of user UUIDs participating in the thread.
        created_at: When the thread was created.
        updated_at: When the thread was last updated.
    """

    __tablename__ = "hilos_mensajes"

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    asunto: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    participantes: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    ultimo_mensaje_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<HiloMensaje id={self.id} asunto='{self.asunto}' "
            f"participantes={len(self.participantes)}>"
        )
