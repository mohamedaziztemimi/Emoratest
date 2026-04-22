"""Add semantic event enrichment fields

Revision ID: 013_add_semantic_fields
Revises: 012_flag_exposure
Create Date: 2026-04-22

Adds business-readable fields to events table:
- label: Human-readable text from element (innerText, aria-label, alt)
- element_type: Semantic type (button, link, input, image, container)
- section: Page section (hero, navbar, footer, pricing, etc.)
- selector: Full CSS selector for element identification
- Updates type constraint to include 'mouse_summary'
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '013_add_semantic_fields'
down_revision: Union[str, None] = '012_flag_exposure'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to events table
    op.add_column('events', sa.Column('label', sa.String(256), nullable=True))
    op.add_column('events', sa.Column('element_type', sa.String(32), nullable=True))
    op.add_column('events', sa.Column('section', sa.String(64), nullable=True))
    op.add_column('events', sa.Column('selector', sa.String(512), nullable=True))

    # Drop old type constraint
    op.execute("ALTER TABLE events DROP CONSTRAINT IF EXISTS ck_events_type")

    # Add updated type constraint with 'mouse_summary'
    op.execute("""
        ALTER TABLE events
        ADD CONSTRAINT ck_events_type
        CHECK (type IN ('mouse_move','click','scroll','exit_intent','visibility','mouse_summary'))
    """)

    # Create index on label for faster lookups (useful for filtering by button text, etc.)
    op.create_index('ix_events_label', 'events', ['label'], unique=False)
    op.create_index('ix_events_element_type', 'events', ['element_type'], unique=False)
    op.create_index('ix_events_section', 'events', ['section'], unique=False)


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_events_section', table_name='events')
    op.drop_index('ix_events_element_type', table_name='events')
    op.drop_index('ix_events_label', table_name='events')

    # Drop updated type constraint
    op.execute("ALTER TABLE events DROP CONSTRAINT IF EXISTS ck_events_type")

    # Add back original type constraint
    op.execute("""
        ALTER TABLE events
        ADD CONSTRAINT ck_events_type
        CHECK (type IN ('mouse_move','click','scroll','exit_intent','visibility'))
    """)

    # Remove columns
    op.drop_column('events', 'selector')
    op.drop_column('events', 'section')
    op.drop_column('events', 'element_type')
    op.drop_column('events', 'label')
