"""Update free plan session limit from 500 to 2000

Revision ID: 023_update_free_plan_limit
Revises: 022_add_environment_to_sessions
Create Date: 2026-05-05

Increases the default monthly session limit for free plan from 500 to 2000.
Also updates existing free plan merchants to the new limit.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '023_update_free_plan_limit'
down_revision: Union[str, None] = '022_add_environment_to_sessions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Update existing free and trial plan merchants from 500 to 2000
    op.execute(
        sa.text("UPDATE merchants SET monthly_session_limit = 2000 WHERE plan IN ('free', 'trial') AND monthly_session_limit = 500")
    )
    # Change the default for new merchants
    op.alter_column(
        'merchants',
        'monthly_session_limit',
        server_default='2000'
    )


def downgrade() -> None:
    # Revert existing free plan merchants back to 500
    op.execute(
        sa.text("UPDATE merchants SET monthly_session_limit = 500 WHERE plan = 'free' AND monthly_session_limit = 2000")
    )
    # Change the default back to 500
    op.alter_column(
        'merchants',
        'monthly_session_limit',
        server_default='500'
    )
