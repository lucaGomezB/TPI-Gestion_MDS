"""010: Create avisos and acknowledgments_avisos tables (C-12).

Creates the two tables for the system notice board (tablon de avisos):

- ``avisos``: time-scoped notices with configurable alcance and severidad
- ``acknowledgments_avisos``: immutable acknowledgment audit log (RN-19)

Includes:
- FK to tenants, materias (nullable), cohortes (nullable), usuarios
- Composite index (tenant_id, inicio_en, fin_en, activo) for visibility queries
- Unique constraint (aviso_id, usuario_id) on acknowledgments for idempotency

Revision ID: f6a7b8c9d0e1
Revises: f0a1b2c3d4e5
Create Date: 2026-06-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "f0a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create avisos and acknowledgments_avisos tables."""

    # ── avisos ─────────────────────────────────────────────────────────
    op.create_table(
        "avisos",
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
            "alcance",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("materias.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("cohortes.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "rol_destino",
            sa.String(20),
            nullable=True,
        ),
        sa.Column(
            "severidad",
            sa.String(20),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("cuerpo", sa.Text, nullable=False),
        sa.Column(
            "inicio_en",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "fin_en",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "orden",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "activo",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "requiere_ack",
            sa.Boolean,
            nullable=False,
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

    # ── acknowledgments_avisos ─────────────────────────────────────────
    op.create_table(
        "acknowledgments_avisos",
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
            "aviso_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("avisos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "leido_en",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    # ── Indexes ────────────────────────────────────────────────────────
    op.create_index(
        "ix_avisos_tenant_vigencia_activo",
        "avisos",
        ["tenant_id", "inicio_en", "fin_en", "activo"],
    )
    op.create_index(
        "ix_avisos_tenant_alcance",
        "avisos",
        ["tenant_id", "alcance"],
    )
    op.create_index(
        "ix_ack_aviso_id",
        "acknowledgments_avisos",
        ["aviso_id"],
    )
    op.create_index(
        "ix_ack_usuario_id",
        "acknowledgments_avisos",
        ["usuario_id"],
    )

    # Unique constraint for idempotency (D-04)
    op.create_unique_constraint(
        "uq_ack_aviso_usuario",
        "acknowledgments_avisos",
        ["aviso_id", "usuario_id"],
    )


def downgrade() -> None:
    """Drop acknowledgments_avisos and avisos tables."""
    op.drop_constraint(
        "uq_ack_aviso_usuario",
        "acknowledgments_avisos",
    )
    op.drop_index("ix_ack_usuario_id", table_name="acknowledgments_avisos")
    op.drop_index("ix_ack_aviso_id", table_name="acknowledgments_avisos")
    op.drop_index("ix_avisos_tenant_alcance", table_name="avisos")
    op.drop_index("ix_avisos_tenant_vigencia_activo", table_name="avisos")
    op.drop_table("acknowledgments_avisos")
    op.drop_table("avisos")
