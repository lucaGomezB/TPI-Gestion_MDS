"""014: Create facturas table for teacher invoice management (C-20).

Creates the ``facturas`` table per E20 with indexes for query patterns:
- (tenant_id, periodo) for period browsing
- (usuario_id) for own-history lookups
- (tenant_id, estado) for admin filtering by state

Revision ID: a3b4c5d6e7f8
Revises: a2b3c4d5e6f7
Create Date: 2026-06-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f8"
down_revision: str | None = "a2b3c4d5e6f7"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create facturas table with indexes."""

    op.create_table(
        "facturas",
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
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("detalle", sa.String(500), nullable=False),
        sa.Column("referencia_archivo", sa.String(500), nullable=False),
        sa.Column(
            "tamano_kb",
            sa.Numeric(10, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "estado",
            sa.String(10),
            nullable=False,
            server_default=sa.text("'Pendiente'"),
        ),
        sa.Column(
            "cargada_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "abonada_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Indexes for query patterns
    op.create_index(
        "ix_facturas_tenant_periodo",
        "facturas",
        ["tenant_id", "periodo"],
    )
    op.create_index(
        "ix_facturas_usuario_id",
        "facturas",
        ["usuario_id"],
    )
    op.create_index(
        "ix_facturas_tenant_estado",
        "facturas",
        ["tenant_id", "estado"],
    )


def downgrade() -> None:
    """Drop facturas table."""
    op.drop_index("ix_facturas_tenant_estado", table_name="facturas")
    op.drop_index("ix_facturas_usuario_id", table_name="facturas")
    op.drop_index("ix_facturas_tenant_periodo", table_name="facturas")
    op.drop_table("facturas")
