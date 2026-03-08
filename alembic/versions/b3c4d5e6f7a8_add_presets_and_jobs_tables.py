"""add presets and jobs tables

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-08 08:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('presets',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('folder_path', sa.String(length=500), nullable=False),
    sa.Column('host_a_id', sa.Integer(), nullable=False),
    sa.Column('host_b_id', sa.Integer(), nullable=False),
    sa.Column('style_id', sa.Integer(), nullable=False),
    sa.Column('personality_guidance', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['host_a_id'], ['hosts.id'], ),
    sa.ForeignKeyConstraint(['host_b_id'], ['hosts.id'], ),
    sa.ForeignKeyConstraint(['style_id'], ['styles.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('folder_path')
    )

    op.create_table('jobs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_file', sa.String(length=500), nullable=False),
    sa.Column('preset_id', sa.Integer(), nullable=False),
    sa.Column('state', sa.String(length=20), nullable=False, server_default='pending'),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['preset_id'], ['presets.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('jobs')
    op.drop_table('presets')
