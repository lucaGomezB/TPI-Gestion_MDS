"""004: Add academic structure tables — carreras, cohortes, materias, programas_materia.

Creates the four core academic entity tables with proper FKs, indexes,
and unique constraints.

Revision ID: e1f2a3b4c5d6
Revises: f7a8b9c0d1e2
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: str | None = "f7a8b9c0d1e2"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create carreras, cohortes, materias, programas_materia tables."""

    # ── carreras ─────────────────────────────────────────────────────
    op.create_table(
        "carreras",
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
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'Activa'"),
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
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "tenant_id", "codigo", name="uq_carrera_tenant_codigo"
        ),
    )

    # ── cohortes ─────────────────────────────────────────────────────
    op.create_table(
        "cohortes",
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
            "carrera_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("carreras.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("anio", sa.Integer, nullable=False),
        sa.Column("vig_desde", sa.Date, nullable=False),
        sa.Column("vig_hasta", sa.Date, nullable=True),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'Activa'"),
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
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "tenant_id", "carrera_id", "nombre",
            name="uq_cohorte_tenant_carrera_nombre",
        ),
    )

    # ── materias ─────────────────────────────────────────────────────
    op.create_table(
        "materias",
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
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'Activa'"),
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
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "tenant_id", "codigo", name="uq_materia_tenant_codigo"
        ),
    )

    # ── programas_materia ─────────────────────────────────────────────
    op.create_table(
        "programas_materia",
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
            "carrera_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("carreras.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("cohortes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("referencia_archivo", sa.String(500), nullable=False),
        sa.Column(
            "cargado_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── Indexes for programas_materia ──────────────────────────────────
    op.create_index(
        "ix_programas_materia_materia_id",
        "programas_materia",
        ["materia_id"],
    )
    op.create_index(
        "ix_programas_materia_carrera_id",
        "programas_materia",
        ["carrera_id"],
    )
    op.create_index(
        "ix_programas_materia_cohorte_id",
        "programas_materia",
        ["cohorte_id"],
    )


def downgrade() -> None:
    """Drop all four tables (FK order: programas_materia, materias, cohortes, carreras)."""
    op.drop_index("ix_programas_materia_cohorte_id", table_name="programas_materia")
    op.drop_index("ix_programas_materia_carrera_id", table_name="programas_materia")
    op.drop_index("ix_programas_materia_materia_id", table_name="programas_materia")
    op.drop_table("programas_materia")
    op.drop_table("materias")
    op.drop_table("cohortes")
    op.drop_table("carreras")
