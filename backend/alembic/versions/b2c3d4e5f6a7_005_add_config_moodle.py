"""005: Add config_moodle JSONB column to tenants table.

Revision ID: b2c3d4e5f6a7
Revises: e1f2a3b4c5d6
Create Date: 2026-06-04 08:45:00

Adds a nullable JSONB column ``config_moodle`` to the ``tenants`` table
for storing per-tenant Moodle Web Services configuration (with encrypted
ws_url and ws_token fields).
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "e1f2a3b4c5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("config_moodle", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tenants", "config_moodle")
