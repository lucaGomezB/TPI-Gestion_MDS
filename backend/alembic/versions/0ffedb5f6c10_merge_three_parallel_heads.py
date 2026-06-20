"""merge three parallel heads

Revision ID: 0ffedb5f6c10
Revises: a3b4c5d6e7f8, e6f7a8b9c0d1, g1h2i3j4k5l6
Create Date: 2026-06-19 17:59:15.068892
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ffedb5f6c10'
down_revision: Union[str, None] = ('a3b4c5d6e7f8', 'e6f7a8b9c0d1', 'g1h2i3j4k5l6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
