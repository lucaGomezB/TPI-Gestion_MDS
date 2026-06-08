"""Asignacion model — user-role-context temporal link.

An Asignacion links a Usuario to a Rol within an academic context
(Materia, Carrera, Cohorte, Comisiones) with temporal validity
(vig_desde / vig_hasta).

Design decisions (per C-05 design.md):
- D-01: No AuditMixin — state derived from dates, not estado column.
- D-02: vig_desde (NOT NULL), vig_hasta (nullable) for temporal validity.
- D-03: comisiones as JSONB list[str], default [].
- D-04: Nullable academic FKs — all null = tenant-level role.
- D-05: responsable_id FK to usuarios.id (not to asignaciones), nullable.
"""

from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TenantMixin, TimestampMixin


class Asignacion(AppModel, TimestampMixin, TenantMixin):
    """A user assigned to a role within an academic context with temporal validity.

    Per D-01 this model does NOT inherit AuditMixin — there is no ``estado``
    column.  The effective state (Pendiente / Vigente / Vencida) is derived
    from ``vig_desde`` and ``vig_hasta`` at query time.
    """

    __tablename__ = "asignaciones"

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    materia_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materias.id", ondelete="SET NULL"),
        nullable=True,
    )
    carrera_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("carreras.id", ondelete="SET NULL"),
        nullable=True,
    )
    cohorte_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("cohortes.id", ondelete="SET NULL"),
        nullable=True,
    )
    comisiones: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    responsable_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    vig_desde: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    vig_hasta: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
