"""Create session_feedback table and add survey config to merchants

Revision ID: 021_create_session_feedback
Revises: 020_consolidate_emotions
Create Date: 2026-05-02

Adds:
- session_feedback table: stores user feedback from micro-survey widget
- merchant survey config fields: survey_enabled, survey_trigger, survey_sample_rate, survey_pages
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '021_create_session_feedback'
down_revision: Union[str, None] = '020_consolidate_emotions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Create session_feedback table
    op.create_table(
        'session_feedback',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False
        ),
        sa.Column(
            'session_id',
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),
        sa.Column(
            'merchant_id',
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),
        sa.Column('rating', sa.String(16), nullable=False),
        sa.Column('page_url', sa.Text(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['session_id'], ['sessions.id'],
            name='fk_session_feedback_session_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['merchant_id'], ['merchants.id'],
            name='fk_session_feedback_merchant_id',
            ondelete='CASCADE'
        ),
        sa.CheckConstraint(
            "rating IN ('negative','neutral','positive')",
            name='ck_session_feedback_rating'
        )
    )
    op.create_index('ix_session_feedback_session_id', 'session_feedback', ['session_id'])
    op.create_index('ix_session_feedback_merchant_id', 'session_feedback', ['merchant_id'])
    op.create_index('ix_session_feedback_created_at', 'session_feedback', ['created_at'])

    # Add survey config columns to merchants table
    op.add_column(
        'merchants',
        sa.Column(
            'survey_enabled',
            sa.Boolean(),
            server_default='false',
            nullable=False
        )
    )
    op.add_column(
        'merchants',
        sa.Column(
            'survey_trigger',
            sa.String(32),
            server_default='exit_intent',
            nullable=False
        )
    )
    op.add_column(
        'merchants',
        sa.Column(
            'survey_sample_rate',
            sa.Float(),
            server_default='0.1',
            nullable=False
        )
    )
    op.add_column(
        'merchants',
        sa.Column(
            'survey_pages',
            postgresql.JSONB(),
            nullable=True
        )
    )

    # Add check constraint for survey_trigger
    op.execute("""
        ALTER TABLE merchants
        ADD CONSTRAINT ck_merchants_survey_trigger
        CHECK (survey_trigger IN ('exit_intent', 'scroll_75', 'time_30s'))
    """)


def downgrade() -> None:
    # Drop survey config columns from merchants
    op.execute("ALTER TABLE merchants DROP CONSTRAINT ck_merchants_survey_trigger")
    op.drop_column('merchants', 'survey_pages')
    op.drop_column('merchants', 'survey_sample_rate')
    op.drop_column('merchants', 'survey_trigger')
    op.drop_column('merchants', 'survey_enabled')

    # Drop session_feedback table
    op.drop_index('ix_session_feedback_created_at', table_name='session_feedback')
    op.drop_index('ix_session_feedback_merchant_id', table_name='session_feedback')
    op.drop_index('ix_session_feedback_session_id', table_name='session_feedback')
    op.drop_table('session_feedback')
