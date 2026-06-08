"""008: Create versiones_padron and entradas_padron tables.

Creates the two tables for the padron de alumnos (C-06):

- ``versiones_padron``: import versions, one active per (materia, cohorte)
- ``entradas_padron``: individual student records within a version

Includes:
- FKs to materias, cohortes, usuarios
- Partial unique index on activa=True per (materia_id, cohorte_id)
- Composite index (materia_id, cohorte_id, activa) for lookup queries
- Email column as TEXT (EncryptedString maps to Text at DB level)

Revision ID: d5e6f7a8b9c0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d5e6f7a8b9c0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create versiones_padron and entradas_padron tables."""

    # ── versiones_padron ──────────────────────────────────────────────
    op.create_table(
        "versiones_padron",
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
            "cohorte_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("cohortes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cargado_por",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "cargado_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("activa", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "total_entradas",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
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

    # ── entradas_padron ───────────────────────────────────────────────
    op.create_table(
        "entradas_padron",
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
            "version_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("versiones_padron.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("apellidos", sa.String(150), nullable=False),
        sa.Column("email", sa.Text, nullable=False),  # EncryptedString -> TEXT
        sa.Column("comision", sa.String(50), nullable=True),
        sa.Column("regional", sa.String(100), nullable=True),
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

    # ── Indexes ───────────────────────────────────────────────────────
    op.create_index(
        "ix_versiones_padron_materia_cohorte_activa",
        "versiones_padron",
        ["materia_id", "cohorte_id", "activa"],
    )
    op.create_index(
        "ix_versiones_padron_materia_id",
        "versiones_padron",
        ["materia_id"],
    )
    op.create_index(
        "ix_entradas_padron_version_id",
        "entradas_padron",
        ["version_id"],
    )
    op.create_index(
        "ix_entradas_padron_usuario_id",
        "entradas_padron",
        ["usuario_id"],
    )


def downgrade() -> None:
    """Drop entradas_padron and versiones_padron tables."""
    op.drop_index("ix_entradas_padron_usuario_id", table_name="entradas_padron")
    op.drop_index("ix_entradas_padron_version_id", table_name="entradas_padron")
    op.drop_index("ix_versiones_padron_materia_id", table_name="versiones_padron")
    op.drop_index(
        "ix_versiones_padron_materia_cohorte_activa",
        table_name="versiones_padron",
    )
    op.drop_table("entradas_padron")
    op.drop_table("versiones_padron")
