"""009: Create calificaciones and umbrales_materia tables.

Creates the two tables for the calificaciones (grades) system (C-07):

- ``calificaciones``: individual grade records per student per activity
- ``umbrales_materia``: configurable approval thresholds per (asignacion, materia)

Includes:
- FK to entradas_padron (CASCADE) — grades deleted when padron entry is removed
- FK to materias (CASCADE)
- FK to usuarios (SET NULL) for cargado_por
- FK to asignaciones (CASCADE) for umbrales_materia
- Composite index (materia_id, actividad) for grade listing queries
- Composite index (materia_id, cargado_por) for scope-isolated DELETE
- Unique constraint (asignacion_id, materia_id) on umbrales_materia
- JSONB column for valores_aprobatorios

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-06-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: str | None = "d5e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create calificaciones and umbrales_materia tables."""

    # ── calificaciones ────────────────────────────────────────────────
    op.create_table(
        "calificaciones",
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
            "entrada_padron_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("entradas_padron.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("materias.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actividad", sa.String(200), nullable=False),
        sa.Column(
            "nota_numerica",
            sa.Numeric(5, 2),
            nullable=True,
        ),
        sa.Column(
            "nota_textual",
            sa.String(100),
            nullable=True,
        ),
        sa.Column("aprobado", sa.Boolean, nullable=False),
        sa.Column(
            "origen",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'Importado'"),
        ),
        sa.Column(
            "cargado_por",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "importado_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
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

    # ── umbrales_materia ──────────────────────────────────────────────
    op.create_table(
        "umbrales_materia",
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
            "asignacion_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("asignaciones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("materias.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "umbral_pct",
            sa.Integer,
            nullable=False,
            server_default=sa.text("60"),
        ),
        sa.Column(
            "valores_aprobatorios",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[\"Satisfactorio\", \"Supera lo esperado\"]'::jsonb"),
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

    # ── Indexes ───────────────────────────────────────────────────────
    op.create_index(
        "ix_calificaciones_materia_actividad",
        "calificaciones",
        ["materia_id", "actividad"],
    )
    op.create_index(
        "ix_calificaciones_materia_cargado_por",
        "calificaciones",
        ["materia_id", "cargado_por"],
    )
    op.create_index(
        "ix_calificaciones_entrada_padron_id",
        "calificaciones",
        ["entrada_padron_id"],
    )
    op.create_index(
        "ix_calificaciones_cargado_por",
        "calificaciones",
        ["cargado_por"],
    )
    op.create_index(
        "ix_umbrales_materia_materia_id",
        "umbrales_materia",
        ["materia_id"],
    )

    # ── Unique constraint on umbrales_materia ─────────────────────────
    op.create_unique_constraint(
        "uq_umbral_asignacion_materia",
        "umbrales_materia",
        ["asignacion_id", "materia_id"],
    )


def downgrade() -> None:
    """Drop calificaciones and umbrales_materia tables."""
    op.drop_constraint(
        "uq_umbral_asignacion_materia",
        "umbrales_materia",
    )
    op.drop_index("ix_umbrales_materia_materia_id", table_name="umbrales_materia")
    op.drop_index("ix_calificaciones_cargado_por", table_name="calificaciones")
    op.drop_index(
        "ix_calificaciones_entrada_padron_id",
        table_name="calificaciones",
    )
    op.drop_index(
        "ix_calificaciones_materia_cargado_por",
        table_name="calificaciones",
    )
    op.drop_index(
        "ix_calificaciones_materia_actividad",
        table_name="calificaciones",
    )
    op.drop_table("umbrales_materia")
    op.drop_table("calificaciones")
