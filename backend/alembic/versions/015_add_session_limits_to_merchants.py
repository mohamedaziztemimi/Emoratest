"""Add session limit columns to merchants table

Revision ID: 015_add_session_limits
Revises: 014_event_enriched
Create Date: 2026-04-25

Adds monthly session tracking and limits for merchants:
- monthly_session_limit: Max sessions per month (default 500)
- sessions_this_month: Count of sessions in current month
- session_month: Current tracking month
- session_year: Current tracking year
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '015_add_session_limits'
down_revision: Union[str, None] = '014_event_enriched'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        'merchants',
        sa.Column('monthly_session_limit', sa.Integer(), nullable=False, server_default='500')
    )
    op.add_column(
        'merchants',
        sa.Column('sessions_this_month', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'merchants',
        sa.Column('session_month', sa.Integer(), nullable=False, server_default=sa.text('EXTRACT(MONTH FROM NOW())::INTEGER'))
    )
    op.add_column(
        'merchants',
        sa.Column('session_year', sa.Integer(), nullable=False, server_default=sa.text('EXTRACT(YEAR FROM NOW())::INTEGER'))
    )


def downgrade() -> None:
    op.drop_column('merchants', 'session_year')
    op.drop_column('merchants', 'session_month')
    op.drop_column('merchants', 'sessions_this_month')
    op.drop_column('merchants', 'monthly_session_limit')
