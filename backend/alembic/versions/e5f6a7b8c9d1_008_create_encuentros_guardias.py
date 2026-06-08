"""008: Create encuentros and guardias tables (C-14).

Creates the following tables:
- ``slots_encuentro`` — recurring slot templates
- ``instancias_encuentro`` — concrete encuentro instances
- ``guardias`` — duty/office hour records

Each table includes:
- UUID primary key
- tenant_id FK with CASCADE
- Academic entity FKs (materia_id, asignacion_id, etc.)
- Timestamp columns (created_at, updated_at)
- Audit columns (estado, deleted_at) where applicable
- Proper indexes for query patterns

Revision ID: e5f6a7b8c9d1
Revises: d4e5f6a7b8c9
Create Date: 2026-06-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d1"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create slots_encuentro, instancias_encuentro, guardias tables."""

    # ── slots_encuentro ──────────────────────────────────────────────
    op.create_table(
        "slots_encuentro",
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
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("hora", sa.Time, nullable=False),
        sa.Column("dia_semana", sa.String(10), nullable=False),
        sa.Column("fecha_inicio", sa.Date, nullable=False),
        sa.Column(
            "cant_semanas",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("fecha_unica", sa.Date, nullable=True),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("vig_desde", sa.Date, nullable=False),
        sa.Column("vig_hasta", sa.Date, nullable=True),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'Activo'"),
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
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
        "ix_slots_encuentro_materia_id",
        "slots_encuentro",
        ["materia_id"],
    )
    op.create_index(
        "ix_slots_encuentro_tenant_materia",
        "slots_encuentro",
        ["tenant_id", "materia_id"],
    )

    # ── instancias_encuentro ─────────────────────────────────────────
    op.create_table(
        "instancias_encuentro",
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
            "slot_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("slots_encuentro.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("materias.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fecha", sa.Date, nullable=False),
        sa.Column("hora", sa.Time, nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'Programado'"),
        ),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("comentario", sa.Text, nullable=True),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
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
        "ix_instancias_encuentro_materia_id",
        "instancias_encuentro",
        ["materia_id"],
    )
    op.create_index(
        "ix_instancias_encuentro_slot_id",
        "instancias_encuentro",
        ["slot_id"],
    )
    op.create_index(
        "ix_instancias_encuentro_tenant_materia_fecha",
        "instancias_encuentro",
        ["tenant_id", "materia_id", "fecha"],
    )

    # ── guardias ─────────────────────────────────────────────────────
    op.create_table(
        "guardias",
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
        sa.Column("dia", sa.String(10), nullable=False),
        sa.Column("horario", sa.String(50), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'Pendiente'"),
        ),
        sa.Column("comentarios", sa.Text, nullable=True),
        sa.Column(
            "creada_at",
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

    op.create_index(
        "ix_guardias_materia_id",
        "guardias",
        ["materia_id"],
    )
    op.create_index(
        "ix_guardias_tenant_materia_estado",
        "guardias",
        ["tenant_id", "materia_id", "estado"],
    )


def downgrade() -> None:
    """Drop all three tables (reverse FK order)."""
    op.drop_index("ix_guardias_tenant_materia_estado", table_name="guardias")
    op.drop_index("ix_guardias_materia_id", table_name="guardias")
    op.drop_table("guardias")

    op.drop_index(
        "ix_instancias_encuentro_tenant_materia_fecha",
        table_name="instancias_encuentro",
    )
    op.drop_index(
        "ix_instancias_encuentro_slot_id",
        table_name="instancias_encuentro",
    )
    op.drop_index(
        "ix_instancias_encuentro_materia_id",
        table_name="instancias_encuentro",
    )
    op.drop_table("instancias_encuentro")

    op.drop_index(
        "ix_slots_encuentro_tenant_materia",
        table_name="slots_encuentro",
    )
    op.drop_index(
        "ix_slots_encuentro_materia_id",
        table_name="slots_encuentro",
    )
    op.drop_table("slots_encuentro")
