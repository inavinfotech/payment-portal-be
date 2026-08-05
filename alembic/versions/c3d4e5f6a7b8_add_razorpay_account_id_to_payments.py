"""add_razorpay_account_id_to_payments

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-08-05 10:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add razorpay_account_id column to payments table."""
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('razorpay_account_id', sa.String(), nullable=True))
        batch_op.create_foreign_key(
            'fk_payments_razorpay_account_id',
            'razorpay_accounts',
            ['razorpay_account_id'],
            ['id']
        )


def downgrade() -> None:
    """Remove razorpay_account_id column from payments table."""
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_constraint('fk_payments_razorpay_account_id', type_='foreignkey')
        batch_op.drop_column('razorpay_account_id')
