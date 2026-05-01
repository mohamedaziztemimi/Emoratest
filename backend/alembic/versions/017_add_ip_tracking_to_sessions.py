"""Add IP address and user agent tracking to sessions

Revision ID: 017_add_ip_tracking
Revises: 016_password_reset
Create Date: 2026-05-01

Adds tracking fields for better session identification:
- ip_address: Client IP address (extracted from CF-Connecting-IP, X-Forwarded-For, etc.)
- user_agent: Browser user agent string
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '017_add_ip_tracking'
down_revision: Union[str, None] = '016_password_reset'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        'sessions',
        sa.Column('ip_address', sa.String(45), nullable=True)
    )
    op.add_column(
        'sessions',
        sa.Column('user_agent', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('sessions', 'user_agent')
    op.drop_column('sessions', 'ip_address')
