"""003: Create audit_log table — append-only audit trail.

Creates the ``audit_log`` table with:
- All columns per E-AUD (04_modelo_de_datos.md)
- ``search_vector`` TSVECTOR generated column for full-text search
- 5 B-tree indexes with tenant_id prefix for tenant isolation
- 1 GIN index on ``search_vector``
- Append-only triggers ``trg_reject_audit_update`` and ``trg_reject_audit_delete``

Revision ID: f7a8b9c0d1e2
Revises: a1b2c3d4e5f6
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f7a8b9c0d1e2"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create audit_log table with indexes, generated column, and triggers."""

    # ── audit_log table ─────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
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
            "fecha_hora",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "impersonado_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
        sa.Column(
            "accion",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "detalle",
            postgresql.JSONB,
            nullable=True,
        ),
        sa.Column(
            "filas_afectadas",
            sa.Integer,
            nullable=True,
        ),
        sa.Column(
            "ip",
            sa.String(45),
            nullable=True,
        ),
        sa.Column(
            "user_agent",
            sa.String(500),
            nullable=True,
        ),
    )

    # ── Generated column for full-text search ───────────────────────────────
    op.execute(
        """
        ALTER TABLE audit_log ADD COLUMN search_vector TSVECTOR
            GENERATED ALWAYS AS (
                to_tsvector('spanish',
                    coalesce(accion, '') || ' ' ||
                    coalesce(detalle::text, '') || ' ' ||
                    coalesce(ip, '')
                )
            ) STORED;
        """
    )

    # ── B-tree indexes for filtering ────────────────────────────────────────
    op.create_index(
        "ix_audit_log_tenant_fecha",
        "audit_log",
        [sa.text("tenant_id"), sa.text("fecha_hora DESC")],
    )
    op.create_index(
        "ix_audit_log_tenant_accion",
        "audit_log",
        ["tenant_id", "accion"],
    )
    op.create_index(
        "ix_audit_log_tenant_actor",
        "audit_log",
        [sa.text("tenant_id"), sa.text("actor_id"), sa.text("fecha_hora DESC")],
    )
    op.create_index(
        "ix_audit_log_tenant_materia",
        "audit_log",
        [sa.text("tenant_id"), sa.text("materia_id"), sa.text("fecha_hora DESC")],
    )
    op.create_index(
        "ix_audit_log_tenant_ip",
        "audit_log",
        ["tenant_id", "ip"],
    )

    # ── GIN index for full-text search ──────────────────────────────────────
    op.create_index(
        "ix_audit_log_search_vector",
        "audit_log",
        [sa.text("search_vector")],
        postgresql_using="gin",
    )

    # ── Append-only triggers ────────────────────────────────────────────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION reject_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only: UPDATE and DELETE are forbidden';
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_reject_audit_update
            BEFORE UPDATE ON audit_log
            FOR EACH ROW EXECUTE FUNCTION reject_audit_modification();
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_reject_audit_delete
            BEFORE DELETE ON audit_log
            FOR EACH ROW EXECUTE FUNCTION reject_audit_modification();
        """
    )


def downgrade() -> None:
    """Drop audit_log table, triggers, function, and indexes."""

    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS trg_reject_audit_update ON audit_log;")
    op.execute("DROP TRIGGER IF EXISTS trg_reject_audit_delete ON audit_log;")
    op.execute("DROP FUNCTION IF EXISTS reject_audit_modification();")

    # Drop indexes
    op.drop_index("ix_audit_log_search_vector", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_ip", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_materia", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_actor", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_accion", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_fecha", table_name="audit_log")

    # Drop the table (generated column is dropped implicitly)
    op.drop_table("audit_log")
