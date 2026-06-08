"""013: Create liquidaciones table for salary settlements (C-19).

Creates the ``liquidaciones`` table per E19 with indexes and unique
constraint for (cohorte, usuario, periodo) per RN-37.

Revision ID: a2b3c4d5e6f7
Revises: b1c2d3e4f5a6, e6f7a8b9c0d1, g1h2i3j4k5l6
Create Date: 2026-06-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: str | None = "b1c2d3e4f5a6"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create liquidaciones table with indexes and constraints."""

    op.create_table(
        "liquidaciones",
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
            "cohorte_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("cohortes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("comisiones", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("monto_base", sa.Numeric(12, 2), nullable=False),
        sa.Column("monto_plus", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("es_nexo", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "excluido_por_factura",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "estado",
            sa.String(10),
            nullable=False,
            server_default=sa.text("'Abierta'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "cerrada_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "tenant_id", "cohorte_id", "usuario_id", "periodo",
            name="uq_liquidacion_cohorte_usuario_periodo",
        ),
    )

    # Indexes for query patterns
    op.create_index(
        "ix_liquidaciones_periodo",
        "liquidaciones",
        ["tenant_id", "periodo"],
    )
    op.create_index(
        "ix_liquidaciones_cohorte_periodo",
        "liquidaciones",
        ["tenant_id", "cohorte_id", "periodo"],
    )
    op.create_index(
        "ix_liquidaciones_usuario_id",
        "liquidaciones",
        ["usuario_id"],
    )
    op.create_index(
        "ix_liquidaciones_estado",
        "liquidaciones",
        ["tenant_id", "estado"],
    )


def downgrade() -> None:
    """Drop liquidaciones table."""
    op.drop_index("ix_liquidaciones_estado", table_name="liquidaciones")
    op.drop_index("ix_liquidaciones_usuario_id", table_name="liquidaciones")
    op.drop_index("ix_liquidaciones_cohorte_periodo", table_name="liquidaciones")
    op.drop_index("ix_liquidaciones_periodo", table_name="liquidaciones")
    op.drop_table("liquidaciones")
