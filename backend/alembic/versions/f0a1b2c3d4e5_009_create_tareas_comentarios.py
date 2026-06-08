"""009: Create tareas and comentarios_tarea tables (C-16).

Creates the two tables for internal task tracking:
- ``tareas`` — internal tasks assigned between staff (E12)
- ``comentarios_tarea`` — immutable comments on tasks

Includes:
- FK to materias (nullable), usuarios (asignado_a, asignado_por)
- FK from comentarios_tarea to tareas (CASCADE)
- Composite index (tenant_id, estado) on tareas
- Index on tarea_id for comments lookup

Merge of the three 008 branches: padron, encuentros, comunicaciones.
Revision ID: f0a1b2c3d4e5
Revises: d5e6f7a8b9c0, e5f6a7b8c9d0, e5f6a7b8c9d1
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f0a1b2c3d4e5"
down_revision: str | None = ("d5e6f7a8b9c0", "e5f6a7b8c9d0", "e5f6a7b8c9d1")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create tareas and comentarios_tarea tables with indexes."""
    # ── tareas table ───────────────────────────────────────────────────
    op.create_table(
        "tareas",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(), nullable=False),
        sa.Column("materia_id", postgresql.UUID(), nullable=True),
        sa.Column("asignado_a", postgresql.UUID(), nullable=False),
        sa.Column("asignado_por", postgresql.UUID(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Pendiente"),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("contexto_id", postgresql.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["materia_id"],
            ["materias.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["asignado_a"],
            ["usuarios.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["asignado_por"],
            ["usuarios.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tareas_tenant_estado",
        "tareas",
        ["tenant_id", "estado"],
    )
    op.create_index(
        "ix_tareas_asignado_a",
        "tareas",
        ["asignado_a"],
    )
    op.create_index(
        "ix_tareas_materia_id",
        "tareas",
        ["materia_id"],
    )

    # ── comentarios_tarea table ─────────────────────────────────────────
    op.create_table(
        "comentarios_tarea",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(), nullable=False),
        sa.Column("tarea_id", postgresql.UUID(), nullable=False),
        sa.Column("autor_id", postgresql.UUID(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tarea_id"],
            ["tareas.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["autor_id"],
            ["usuarios.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_comentarios_tarea_tarea_id",
        "comentarios_tarea",
        ["tarea_id"],
    )


def downgrade() -> None:
    """Drop comentarios_tarea and tareas tables."""
    op.drop_table("comentarios_tarea")
    op.drop_table("tareas")
