"""001: Create tenants and usuarios tables.

Revision ID: d715beceafc3
Revises: None
Create Date: 2026-06-02 14:53:10

This is the initial schema migration. It creates:

- ``tenants``: Multi-tenant root entity with UUID PK, nombre, JSONB config,
  activo flag, and timestamps.
- ``usuarios``: User accounts with encrypted PII columns (TEXT storage),
  email_hash for deterministic lookups, unique constraint on
  (tenant_id, email_hash), and an index for login lookups.

Encrypted columns (email, dni, cuil, cbu, alias_cbu) are stored as TEXT
because AES-256-GCM output is variable-length base64 strings.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d715beceafc3"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create tenants and usuarios tables."""

    # ── tenants ──────────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column(
            "configuracion",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "activo",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
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

    # ── usuarios ─────────────────────────────────────────────────────
    op.create_table(
        "usuarios",
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
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("apellidos", sa.String(100), nullable=False),
        # PII columns — stored as TEXT (encrypted via AES-256-GCM)
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("email_hash", sa.String(64), nullable=False),
        sa.Column("dni", sa.Text, nullable=True),
        sa.Column("cuil", sa.Text, nullable=True),
        sa.Column("cbu", sa.Text, nullable=True),
        sa.Column("alias_cbu", sa.Text, nullable=True),
        # Non-PII fields
        sa.Column("banco", sa.String(100), nullable=True),
        sa.Column("regional", sa.String(100), nullable=True),
        sa.Column("legajo", sa.String(50), nullable=True),
        sa.Column("legajo_profesional", sa.String(50), nullable=True),
        sa.Column(
            "facturador",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        # Audit columns
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
        # Unique constraint: one email_hash per tenant
        sa.UniqueConstraint(
            "tenant_id",
            "email_hash",
            name="uq_usuario_tenant_email_hash",
        ),
    )

    # ── Indexes ──────────────────────────────────────────────────────
    op.create_index(
        "ix_usuario_tenant_email_hash",
        "usuarios",
        ["tenant_id", "email_hash"],
    )


def downgrade() -> None:
    """Drop usuarios and tenants tables."""
    op.drop_table("usuarios")
    op.drop_table("tenants")
