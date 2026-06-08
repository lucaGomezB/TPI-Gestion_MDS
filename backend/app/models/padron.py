"""Padron de alumnos models — VersionPadron and EntradaPadron.

VersionPadron tracks import versions (one active per materia+cohorte).
EntradaPadron stores individual student records within a version.

Design decisions (per C-06 design.md):
- No AuditMixin — padron models use only TimestampMixin + TenantMixin.
- EntradaPadron.usuario_id is nullable (student may not have an account yet).
- EntradaPadron.email uses EncryptedString (AES-256-GCM) for PII protection.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin
from app.models.types import EncryptedString


class VersionPadron(AppModel, TimestampMixin, TenantMixin):
    """An import version of the student roster for a (materia, cohorte).

    Only one version can be active (``activa=True``) per (materia_id, cohorte_id)
    at any time. When a new version is created, the previous active version is
    set to ``activa=False``.
    """

    __tablename__ = "versiones_padron"

    __table_args__ = (
        # Ensure only one active version per materia+cohorte
        # This is enforced at the application level (PadronService) and
        # backed by a partial unique index in the migration (migration 008).
    )

    # ── Override TenantMixin.tenant_id to be non-nullable ────────────
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    materia_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materias.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cohorte_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("cohortes.id", ondelete="CASCADE"),
        nullable=False,
    )
    cargado_por: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    cargado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    activa: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    total_entradas: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────────
    entradas: Mapped[list["EntradaPadron"]] = relationship(
        "EntradaPadron",
        back_populates="version",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EntradaPadron(AppModel, TimestampMixin, TenantMixin):
    """An individual student record within a VersionPadron.

    Each row represents one student imported from a CSV/XLSX file.
    The ``email`` field is encrypted at rest via ``EncryptedString``.
    The ``usuario_id`` field is nullable — a student may not have a
    system account yet (matching will happen in C-07 calificaciones).
    """

    __tablename__ = "entradas_padron"

    # ── Override TenantMixin.tenant_id to be non-nullable ────────────
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    version_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("versiones_padron.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    apellidos: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        EncryptedString,
        nullable=False,
    )
    comision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    regional: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────────
    version: Mapped["VersionPadron"] = relationship(
        "VersionPadron",
        back_populates="entradas",
    )
    calificaciones: Mapped[list["Calificacion"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        "Calificacion",
        back_populates="entrada_padron",
        lazy="selectin",
    )
