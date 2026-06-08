"""PasswordResetToken model — single-use tokens for password recovery.

Tokens are stored as SHA-256 hashes of the raw random value. Each token
has a 1-hour expiry and can only be used once (``used_at`` is set on
successful consumption).
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel


class PasswordResetToken(AppModel):
    """A single-use, time-limited token for password recovery."""

    __tablename__ = "password_reset_tokens"

    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # ── Indexes ──────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_password_reset_tokens_token_hash", "token_hash"),
    )
