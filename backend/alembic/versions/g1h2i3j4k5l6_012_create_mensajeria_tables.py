"""012: Create mensajeria tables (C-13).

Creates the three tables for internal messaging between teachers and
coordination:

- ``hilos_mensajes``: message threads grouping messages by subject
- ``mensajes``: individual messages within threads
- ``mensajes_eliminados``: per-user soft-delete tracking

Includes:
- FK to tenants, usuarios for all tables
- Composite index (destinatario_id, leido, tenant_id) for unread count queries
- Index on (hilo_id) for thread lookups
- Index on (remitente_id, destinatario_id) for participant queries
- FK CASCADE on hilo delete to clean up messages
- FK CASCADE on mensaje delete to clean up deletion records

Revision ID: g1h2i3j4k5l6
Revises: g0h1i2j3k4l5
Create Date: 2026-06-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "g1h2i3j4k5l6"
down_revision: str | None = "g0h1i2j3k4l5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create hilos_mensajes, mensajes, and mensajes_eliminados tables."""

    # ── hilos_mensajes ─────────────────────────────────────────────────
    op.create_table(
        "hilos_mensajes",
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
            "asunto",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "participantes",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "ultimo_mensaje_at",
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

    # ── mensajes ───────────────────────────────────────────────────────
    op.create_table(
        "mensajes",
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
            "hilo_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("hilos_mensajes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "remitente_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "destinatario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asunto",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "cuerpo",
            sa.Text,
            nullable=False,
        ),
        sa.Column(
            "leido",
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

    # ── mensajes_eliminados ────────────────────────────────────────────
    op.create_table(
        "mensajes_eliminados",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "mensaje_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("mensajes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── Indexes ────────────────────────────────────────────────────────
    op.create_index(
        "ix_mensajes_destinatario_leido_tenant",
        "mensajes",
        ["destinatario_id", "leido", "tenant_id"],
    )
    op.create_index(
        "ix_mensajes_hilo_id",
        "mensajes",
        ["hilo_id"],
    )
    op.create_index(
        "ix_mensajes_remitente_destinatario",
        "mensajes",
        ["remitente_id", "destinatario_id"],
    )
    op.create_index(
        "ix_mensajes_eliminados_mensaje_id",
        "mensajes_eliminados",
        ["mensaje_id"],
    )


def downgrade() -> None:
    """Drop mensajeria tables in reverse dependency order."""
    op.drop_table("mensajes_eliminados")
    op.drop_table("mensajes")
    op.drop_table("hilos_mensajes")
