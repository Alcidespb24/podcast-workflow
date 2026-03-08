"""add episodes table

Revision ID: a1b2c3d4e5f6
Revises: cf39bf4e68f2
Create Date: 2026-03-08 06:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'cf39bf4e68f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('episodes',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('episode_number', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=300), nullable=False),
    sa.Column('duration_seconds', sa.Float(), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('hosts_json', sa.Text(), nullable=False),
    sa.Column('style_name', sa.String(length=100), nullable=False),
    sa.Column('source_file', sa.String(length=500), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('episodes')
