"""011: Create coloquios tables (C-15).

Creates the following tables:
- ``evaluaciones_coloquio`` — coloquio convocatorias with JSONB days/quota
- ``reservas_coloquio`` — student reservations for coloquio turns
- ``resultados_coloquio`` — student grades/results for coloquio evaluations

Each table includes:
- UUID primary key
- tenant_id FK with CASCADE
- Proper FKs to materias, usuarios, evaluaciones_coloquio
- Timestamp columns (created_at, updated_at)
- Composite indexes for query patterns
- Unique constraints for business rules

Revision ID: g0h1i2j3k4l5
Revises: f6a7b8c9d0e1
Create Date: 2026-06-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "g0h1i2j3k4l5"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create evaluaciones_coloquio, reservas_coloquio, resultados_coloquio tables."""

    # ── evaluaciones_coloquio ──────────────────────────────────────────
    op.create_table(
        "evaluaciones_coloquio",
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
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column(
            "dias",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "creado_por",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "activa",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("cohortes.id", ondelete="SET NULL"),
            nullable=True,
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

    op.create_index(
        "ix_eval_coloquio_tenant_materia",
        "evaluaciones_coloquio",
        ["tenant_id", "materia_id"],
    )

    # ── reservas_coloquio ──────────────────────────────────────────────
    op.create_table(
        "reservas_coloquio",
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
            "evaluacion_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("evaluaciones_coloquio.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "alumno_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dia", sa.Date, nullable=False),
        sa.Column(
            "confirmada",
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

    op.create_index(
        "ix_reserva_coloquio_evaluacion",
        "reservas_coloquio",
        ["evaluacion_id"],
    )
    op.create_index(
        "ix_reserva_coloquio_alumno",
        "reservas_coloquio",
        ["alumno_id"],
    )
    op.create_unique_constraint(
        "uq_reserva_coloquio_eval_alumno",
        "reservas_coloquio",
        ["evaluacion_id", "alumno_id"],
    )

    # ── resultados_coloquio ────────────────────────────────────────────
    op.create_table(
        "resultados_coloquio",
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
            "evaluacion_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("evaluaciones_coloquio.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "alumno_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "nota",
            sa.Numeric(5, 2),
            nullable=True,
        ),
        sa.Column(
            "aprobado",
            sa.Boolean,
            nullable=False,
        ),
        sa.Column(
            "registrado_por",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
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

    op.create_unique_constraint(
        "uq_resultado_coloquio_eval_alumno",
        "resultados_coloquio",
        ["evaluacion_id", "alumno_id"],
    )


def downgrade() -> None:
    """Drop all three tables (reverse FK order)."""
    op.drop_constraint(
        "uq_resultado_coloquio_eval_alumno",
        "resultados_coloquio",
    )
    op.drop_table("resultados_coloquio")

    op.drop_constraint(
        "uq_reserva_coloquio_eval_alumno",
        "reservas_coloquio",
    )
    op.drop_index("ix_reserva_coloquio_alumno", table_name="reservas_coloquio")
    op.drop_index("ix_reserva_coloquio_evaluacion", table_name="reservas_coloquio")
    op.drop_table("reservas_coloquio")

    op.drop_index(
        "ix_eval_coloquio_tenant_materia",
        table_name="evaluaciones_coloquio",
    )
    op.drop_table("evaluaciones_coloquio")
