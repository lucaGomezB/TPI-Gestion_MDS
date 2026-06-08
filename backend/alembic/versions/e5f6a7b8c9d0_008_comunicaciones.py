"""008: Create comunicaciones and lotes_comunicaciones tables (C-11).

Creates the two tables for the communications queue system with all
columns, foreign keys, and 6 composite indexes as defined in D-09.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create lotes_comunicaciones and comunicaciones tables."""
    op.create_table(
        "lotes_comunicaciones",
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
            "materia_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("materias.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "enviado_por",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("asunto", sa.String(500), nullable=False),
        sa.Column("total", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("enviados", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("fallidos", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column(
            "estado", sa.String(30), nullable=False,
            server_default=sa.text("'Pendiente'"),
        ),
        sa.Column(
            "requiere_aprobacion", sa.Boolean, nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "aprobado_por",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("aprobado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "preview_confirmado", sa.Boolean, nullable=False,
            server_default=sa.text("false"),
        ),
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

    op.create_table(
        "comunicaciones",
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
            "lote_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("lotes_comunicaciones.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("materias.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "enviado_por",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("destinatario", sa.Text, nullable=False),
        sa.Column("asunto", sa.String(500), nullable=False),
        sa.Column("cuerpo", sa.Text, nullable=False),
        sa.Column(
            "estado", sa.String(20), nullable=False,
            server_default=sa.text("'Pendiente'"),
        ),
        sa.Column("error_msg", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
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

    # ── Indexes for common query patterns (D-09) ───────────────────────
    op.create_index(
        "ix_comunicaciones_tenant_estado",
        "comunicaciones",
        ["tenant_id", "estado"],
    )
    op.create_index(
        "ix_comunicaciones_lote_id",
        "comunicaciones",
        ["lote_id"],
    )
    op.create_index(
        "ix_comunicaciones_materia_id",
        "comunicaciones",
        ["materia_id"],
    )
    op.create_index(
        "ix_lotes_tenant_estado",
        "lotes_comunicaciones",
        ["tenant_id", "estado"],
    )
    op.create_index(
        "ix_lotes_materia_id",
        "lotes_comunicaciones",
        ["materia_id"],
    )


def downgrade() -> None:
    """Drop comunicaciones and lotes_comunicaciones tables."""
    op.drop_index("ix_lotes_materia_id", table_name="lotes_comunicaciones")
    op.drop_index("ix_lotes_tenant_estado", table_name="lotes_comunicaciones")
    op.drop_index("ix_comunicaciones_materia_id", table_name="comunicaciones")
    op.drop_index("ix_comunicaciones_lote_id", table_name="comunicaciones")
    op.drop_index("ix_comunicaciones_tenant_estado", table_name="comunicaciones")
    op.drop_table("comunicaciones")
    op.drop_table("lotes_comunicaciones")
