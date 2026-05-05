"""Fix session limits for all plans and add unlimited support

Revision ID: 024_fix_limits_add_unlimited
Revises: 023_update_free_plan_limit
Create Date: 2026-05-05

- Ensures all free/trial merchants have 2000 session limit
- Sets growth/scale/enterprise plans to unlimited (-1)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '024_fix_limits_add_unlimited'
down_revision: Union[str, None] = '023_update_free_plan_limit'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Force all free/trial merchants to 2000 (regardless of current value)
    op.execute(
        sa.text("UPDATE merchants SET monthly_session_limit = 2000 WHERE plan IN ('free', 'trial')")
    )
    # Set paid plans to unlimited (-1)
    op.execute(
        sa.text("UPDATE merchants SET monthly_session_limit = -1 WHERE plan IN ('growth', 'scale', 'enterprise')")
    )


def downgrade() -> None:
    # Revert free/trial to 500
    op.execute(
        sa.text("UPDATE merchants SET monthly_session_limit = 500 WHERE plan IN ('free', 'trial')")
    )
    # Revert paid plans to 10000
    op.execute(
        sa.text("UPDATE merchants SET monthly_session_limit = 10000 WHERE plan IN ('growth', 'scale', 'enterprise')")
    )
