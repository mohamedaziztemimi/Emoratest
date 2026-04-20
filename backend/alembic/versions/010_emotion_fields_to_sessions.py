"""add_emotion_fields_to_sessions

Revision ID: 010
Revises: 009
Create Date: 2026-04-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '010_emotion_fields_to_sessions'
down_revision: Union[str, None] = '009_integrations_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sessions',
        sa.Column('primary_emotion', sa.String(length=32), nullable=True)
    )
    op.add_column(
        'sessions',
        sa.Column('emotion_confidence', sa.Float(), nullable=True)
    )
    op.add_column(
        'sessions',
        sa.Column('emotion_scores', postgresql.JSONB(), nullable=True)
    )
    op.add_column(
        'sessions',
        sa.Column('valence', sa.Float(), nullable=True)
    )
    op.add_column(
        'sessions',
        sa.Column('arousal', sa.Float(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('sessions', 'arousal')
    op.drop_column('sessions', 'valence')
    op.drop_column('sessions', 'emotion_scores')
    op.drop_column('sessions', 'emotion_confidence')
    op.drop_column('sessions', 'primary_emotion')
