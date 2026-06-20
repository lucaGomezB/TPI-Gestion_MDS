"""add fechas_evaluacion table

Revision ID: h1i2j3k4l5m6
Revises: 0ffedb5f6c10
Create Date: 2026-06-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "h1i2j3k4l5m6"
down_revision: Union[str, None] = "0ffedb5f6c10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fechas_evaluacion",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("materia_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("materias.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("cohortes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("numero_instancia", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Activo"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "tenant_id", "materia_id", "cohorte_id", "tipo", "numero_instancia",
            name="uq_fecha_eval_tenant_mat_coh_tipo_num",
        ),
    )
    op.create_index("ix_fechas_evaluacion_materia_id", "fechas_evaluacion", ["materia_id"])
    op.create_index("ix_fechas_evaluacion_cohorte_id", "fechas_evaluacion", ["cohorte_id"])


def downgrade() -> None:
    op.drop_table("fechas_evaluacion")
