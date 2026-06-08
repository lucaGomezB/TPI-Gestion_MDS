"""004: Create salary grid tables — salarios_base, salarios_plus, grupos_materia, materias_grupo.

Creates four new tables per E17, E18 and supporting entities:
- ``salarios_base`` — base salary per role with temporal validity (since/hasta)
- ``salarios_plus`` — bonus per (subject group, role) with temporal validity
- ``grupos_materia`` — configurable subject group keys per tenant
- ``materias_grupo`` — N:N join between subjects and groups

Revision ID: b1c2d3e4f5a6
Revises: f7a8b9c0d1e2
Create Date: 2026-06-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "f7a8b9c0d1e2"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create salary grid tables with indexes and constraints."""

    # ── salarios_base ─────────────────────────────────────────────────────
    op.create_table(
        "salarios_base",
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
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("desde", sa.Date, nullable=False),
        sa.Column("hasta", sa.Date, nullable=True),
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
        sa.UniqueConstraint(
            "tenant_id", "rol", "desde",
            name="uq_salario_base_tenant_rol_desde",
        ),
    )

    # Index for vigente queries: (tenant_id, rol, desde, hasta)
    op.create_index(
        "ix_salarios_base_tenant_rol_vigencia",
        "salarios_base",
        ["tenant_id", "rol", "desde", "hasta"],
        postgresql_using="btree",
    )

    # ── salarios_plus ─────────────────────────────────────────────────────
    op.create_table(
        "salarios_plus",
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
        sa.Column("grupo", sa.String(50), nullable=False),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("desde", sa.Date, nullable=False),
        sa.Column("hasta", sa.Date, nullable=True),
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
        sa.UniqueConstraint(
            "tenant_id", "grupo", "rol", "desde",
            name="uq_salario_plus_tenant_grupo_rol_desde",
        ),
    )

    op.create_index(
        "ix_salarios_plus_tenant_grupo_rol_vigencia",
        "salarios_plus",
        ["tenant_id", "grupo", "rol", "desde", "hasta"],
        postgresql_using="btree",
    )

    # ── grupos_materia ────────────────────────────────────────────────────
    op.create_table(
        "grupos_materia",
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
        sa.Column("grupo", sa.String(20), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=True),
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
        sa.UniqueConstraint(
            "tenant_id", "grupo",
            name="uq_grupo_materia_tenant_grupo",
        ),
    )

    op.create_index(
        "ix_grupos_materia_tenant_grupo",
        "grupos_materia",
        ["tenant_id", "grupo"],
        postgresql_using="btree",
    )

    # ── materias_grupo ────────────────────────────────────────────────────
    op.create_table(
        "materias_grupo",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("materias.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "grupo_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("grupos_materia.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "materia_id", "grupo_id",
            name="uq_materia_grupo_materia_grupo",
        ),
    )

    op.create_index(
        "ix_materias_grupo_materia_id",
        "materias_grupo",
        ["materia_id"],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_materias_grupo_grupo_id",
        "materias_grupo",
        ["grupo_id"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Drop salary grid tables in reverse dependency order."""
    op.drop_table("materias_grupo")
    op.drop_table("grupos_materia")
    op.drop_table("salarios_plus")
    op.drop_table("salarios_base")
