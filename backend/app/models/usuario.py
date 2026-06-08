"""Usuario model — represents a person who interacts with the system.

PII fields (email, dni, cuil, cbu, alias_cbu) are stored encrypted via
``EncryptedString`` (AES-256-GCM). A deterministic ``email_hash`` column
(SHA-256 of lowercased email) enables login lookups without decrypting
the email column.

Unique constraint on ``(tenant_id, email_hash)`` ensures unique emails
per tenant. An index on ``(tenant_id, email_hash)`` supports login lookups.
"""

import hashlib

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import AuditMixin, TenantMixin, TimestampMixin
from app.models.types import EncryptedString


class Usuario(AppModel, TimestampMixin, AuditMixin, TenantMixin):
    """A natural person who interacts with the system.

    Inherits from:
        - ``AppModel``: UUID id, auto tablename
        - ``TimestampMixin``: created_at, updated_at
        - ``AuditMixin``: estado (Activo/Inactivo), deleted_at
        - ``TenantMixin``: tenant_id (overridden to non-nullable)
    """

    __tablename__ = "usuarios"

    # ── Override TenantMixin.tenant_id to be non-nullable ────────────
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Non-PII required fields ──────────────────────────────────────
    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    apellidos: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # ── PII fields (encrypted via AES-256-GCM) ───────────────────────
    email: Mapped[str] = mapped_column(
        EncryptedString,
        nullable=False,
    )
    email_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )  # SHA-256 hex digest of lowercased email (for login lookups)

    dni: Mapped[str | None] = mapped_column(
        EncryptedString,
        nullable=True,
    )
    cuil: Mapped[str | None] = mapped_column(
        EncryptedString,
        nullable=True,
    )
    cbu: Mapped[str | None] = mapped_column(
        EncryptedString,
        nullable=True,
    )
    alias_cbu: Mapped[str | None] = mapped_column(
        EncryptedString,
        nullable=True,
    )

    # ── Non-PII optional fields ──────────────────────────────────────
    banco: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    regional: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    legajo: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    legajo_profesional: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ── Auth fields ──────────────────────────────────────────────────
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )  # Argon2id PHC string (nullable for migration)
    totp_secret: Mapped[str | None] = mapped_column(
        EncryptedString,
        nullable=True,
    )  # Encrypted TOTP secret
    totp_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # ── Flags ────────────────────────────────────────────────────────
    facturador: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # ── Constraints and indexes ──────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "email_hash",
            name="uq_usuario_tenant_email_hash",
        ),
        Index(
            "ix_usuario_tenant_email_hash",
            "tenant_id",
            "email_hash",
        ),
    )

    # ── Helpers ──────────────────────────────────────────────────────
    @staticmethod
    def compute_email_hash(email: str) -> str:
        """Return the SHA-256 hex digest of a lowercased email.

        This is the deterministic hash used for login lookups.
        """
        return hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
