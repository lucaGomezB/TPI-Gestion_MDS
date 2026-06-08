"""007: Create asignaciones table for team management (C-05).

Creates the ``asignaciones`` table with all columns, FKs, and 6 indexes
as defined in the C-05 design decisions (D-13).

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create asignaciones table with indexes."""
    op.create_table(
        "asignaciones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("materias.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "carrera_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("carreras.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("cohortes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "comisiones",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "responsable_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("vig_desde", sa.Date, nullable=False),
        sa.Column("vig_hasta", sa.Date, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── Indexes for query patterns (D-13) ─────────────────────────────
    op.create_index(
        "ix_asignaciones_tenant_rol",
        "asignaciones",
        ["tenant_id", "rol"],
    )
    op.create_index(
        "ix_asignaciones_usuario_id",
        "asignaciones",
        ["usuario_id"],
    )
    op.create_index(
        "ix_asignaciones_materia_id",
        "asignaciones",
        ["materia_id"],
    )
    op.create_index(
        "ix_asignaciones_cohorte_id",
        "asignaciones",
        ["cohorte_id"],
    )
    op.create_index(
        "ix_asignaciones_responsable_id",
        "asignaciones",
        ["responsable_id"],
    )
    op.create_index(
        "ix_asignaciones_vigencia",
        "asignaciones",
        ["tenant_id", "vig_desde", "vig_hasta"],
    )


def downgrade() -> None:
    """Drop asignaciones table and all indexes."""
    op.drop_index("ix_asignaciones_vigencia", table_name="asignaciones")
    op.drop_index("ix_asignaciones_responsable_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_cohorte_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_materia_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_usuario_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_tenant_rol", table_name="asignaciones")
    op.drop_table("asignaciones")
