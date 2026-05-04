"""add environment to sessions

Revision ID: 022_add_environment_to_sessions
Revises: 021_create_session_feedback_and_survey_config
Create Date: 2026-05-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '022_add_environment_to_sessions'
down_revision: Union[str, None] = '021_create_session_feedback_and_survey_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add environment column to sessions table
    op.add_column(
        'sessions',
        sa.Column('environment', sa.String(16), nullable=False, server_default='production')
    )

    # Add check constraint for environment values
    op.execute(
        "ALTER TABLE sessions ADD CONSTRAINT ck_sessions_environment "
        "CHECK (environment IN ('test', 'production'))"
    )


def downgrade() -> None:
    # Remove check constraint
    op.execute("ALTER TABLE sessions DROP CONSTRAINT IF EXISTS ck_sessions_environment")

    # Remove environment column
    op.drop_column('sessions', 'environment')
