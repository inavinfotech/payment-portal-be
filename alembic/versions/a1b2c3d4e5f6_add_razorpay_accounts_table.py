"""add_razorpay_accounts_table

Revision ID: a1b2c3d4e5f6
Revises: 57f1bd42e334
Create Date: 2026-07-20 16:27:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '57f1bd42e334'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create razorpay_accounts table and add FK to apps."""
    # Create razorpay_accounts table
    op.create_table('razorpay_accounts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('test_key_id', sa.String(), nullable=False),
        sa.Column('test_key_secret_enc', sa.String(), nullable=False),
        sa.Column('live_key_id', sa.String(), nullable=True),
        sa.Column('live_key_secret_enc', sa.String(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Add razorpay_account_id column to apps table
    with op.batch_alter_table('apps', schema=None) as batch_op:
        batch_op.add_column(sa.Column('razorpay_account_id', sa.String(), nullable=True))
        batch_op.create_foreign_key(
            'fk_apps_razorpay_account_id',
            'razorpay_accounts',
            ['razorpay_account_id'],
            ['id']
        )


def downgrade() -> None:
    """Remove FK from apps and drop razorpay_accounts table."""
    with op.batch_alter_table('apps', schema=None) as batch_op:
        batch_op.drop_constraint('fk_apps_razorpay_account_id', type_='foreignkey')
        batch_op.drop_column('razorpay_account_id')

    op.drop_table('razorpay_accounts')
