"""add_is_live_mode_to_payments

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-06 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_live_mode column to payments table.
    Defaults to False — all existing payments were made in test mode.
    """
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('is_live_mode', sa.Boolean(), nullable=False, server_default=sa.text('0'))
        )


def downgrade() -> None:
    """Remove is_live_mode column from payments table."""
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_column('is_live_mode')
