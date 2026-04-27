"""Add password reset fields to merchants table

Revision ID: 016_password_reset
Revises: 015_add_session_limits
Create Date: 2026-04-25

Adds password reset functionality:
- password_reset_token: Unique token for password reset
- password_reset_expires: Token expiration timestamp
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '016_password_reset'
down_revision: Union[str, None] = '015_add_session_limits'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        'merchants',
        sa.Column('password_reset_token', sa.String(255), nullable=True)
    )
    op.add_column(
        'merchants',
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True)
    )
    # Create index on reset token for faster lookups
    op.create_index(
        'ix_merchants_password_reset_token',
        'merchants',
        ['password_reset_token']
    )


def downgrade() -> None:
    op.drop_index('ix_merchants_password_reset_token', table_name='merchants')
    op.drop_column('merchants', 'password_reset_expires')
    op.drop_column('merchants', 'password_reset_token')
