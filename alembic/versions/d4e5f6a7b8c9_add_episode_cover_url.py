"""add episode cover_url column

Revision ID: d4e5f6a7b8c9
Revises: b3c4d5e6f7a8
Create Date: 2026-03-10 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add cover_url column to episodes table."""
    op.add_column('episodes', sa.Column('cover_url', sa.String(length=500), server_default='', nullable=False))


def downgrade() -> None:
    """Remove cover_url column from episodes table."""
    op.drop_column('episodes', 'cover_url')
