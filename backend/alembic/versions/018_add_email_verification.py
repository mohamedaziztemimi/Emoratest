"""Add email verification fields to merchants

Revision ID: 018_email_verification
Revises: 017_add_ip_tracking
Create Date: 2026-05-01

Adds email verification fields:
- email_verified: Boolean flag for verified status
- email_verification_token: Token sent via email
- email_verification_sent_at: Timestamp for token expiry tracking
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '018_email_verification'
down_revision: Union[str, None] = '017_add_ip_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        'merchants',
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'merchants',
        sa.Column('email_verification_token', sa.String(255), nullable=True)
    )
    op.add_column(
        'merchants',
        sa.Column('email_verification_sent_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        'ix_merchants_email_verification_token',
        'merchants',
        ['email_verification_token'],
        unique=True
    )


def downgrade() -> None:
    op.drop_index('ix_merchants_email_verification_token', table_name='merchants')
    op.drop_column('merchants', 'email_verification_sent_at')
    op.drop_column('merchants', 'email_verification_token')
    op.drop_column('merchants', 'email_verified')
