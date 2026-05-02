"""Create waitlist table

Revision ID: 019_create_waitlist
Revises: 018_email_verification
Create Date: 2026-05-02

Creates waitlist table for users interested in paid plans:
- id: UUID primary key
- email: User email (unique)
- company_name: Optional company name
- plan_interest: Which plan they're interested in
- current_sessions_monthly: Optional current session volume
- message: Optional message from user
- status: pending, contacted, etc
- created_at: Timestamp
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '019_create_waitlist'
down_revision: Union[str, None] = '018_email_verification'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        'waitlist',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False
        ),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('plan_interest', sa.String(32), server_default='growth', nullable=False),
        sa.Column('current_sessions_monthly', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(32), server_default='pending', nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_waitlist_email', 'waitlist', ['email'])


def downgrade() -> None:
    op.drop_index('ix_waitlist_email', table_name='waitlist')
    op.drop_table('waitlist')
