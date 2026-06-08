"""002: Add auth models — roles, usuario_roles, refresh_tokens, password_reset_tokens.

Adds password_hash, totp_secret, totp_enabled columns to usuarios table.
Creates roles, usuario_roles, refresh_tokens, and password_reset_tokens tables.

Revision ID: a1b2c3d4e5f6
Revises: d715beceafc3
Create Date: 2026-06-02

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "d715beceafc3"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Add auth columns and tables."""

    # ── Add columns to usuarios ──────────────────────────────────────
    op.add_column(
        "usuarios",
        sa.Column("password_hash", sa.String(255), nullable=True),
    )
    op.add_column(
        "usuarios",
        sa.Column("totp_secret", sa.Text, nullable=True),
    )
    op.add_column(
        "usuarios",
        sa.Column(
            "totp_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # ── Roles catalog table ───────────────────────────────────────────
    op.create_table(
        "roles",
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
        sa.Column("nombre", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=True),
        sa.Column(
            "permisos",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
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
        sa.UniqueConstraint(
            "tenant_id", "nombre", name="uq_rol_tenant_nombre"
        ),
    )

    # ── User-role assignments table ───────────────────────────────────
    op.create_table(
        "usuario_roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rol_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vigencia_desde",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "vigencia_hasta",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "usuario_id", "rol_id", name="uq_usuario_rol"
        ),
    )

    # ── Refresh tokens table ──────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "token_family",
            postgresql.UUID(as_uuid=False),
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
    )
    op.create_index(
        "ix_refresh_tokens_token_hash",
        "refresh_tokens",
        ["token_hash"],
    )
    op.create_index(
        "ix_refresh_tokens_token_family",
        "refresh_tokens",
        ["token_family"],
    )

    # ── Password reset tokens table ───────────────────────────────────
    op.create_table(
        "password_reset_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
    )


def downgrade() -> None:
    """Reverse all changes — drop tables and columns."""
    op.drop_index("ix_password_reset_tokens_token_hash")
    op.drop_table("password_reset_tokens")
    op.drop_index("ix_refresh_tokens_token_family")
    op.drop_index("ix_refresh_tokens_token_hash")
    op.drop_table("refresh_tokens")
    op.drop_table("usuario_roles")
    op.drop_table("roles")
    op.drop_column("usuarios", "totp_enabled")
    op.drop_column("usuarios", "totp_secret")
    op.drop_column("usuarios", "password_hash")
