"""Create event_enriched table for UI-friendly event display

Revision ID: 014_event_enriched
Revises: 013_add_semantic_fields
Create Date: 2026-04-22

Creates event_enriched table for UI consumption:
- Stores human-readable event descriptions
- Separates UI concerns from raw ML event data
- Includes label, section, element_type, readable_description
- Raw events table remains unchanged for ML pipeline
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '014_event_enriched'
down_revision: Union[str, None] = '013_add_semantic_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "event_enriched",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.BigInteger, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("label", sa.String(256), nullable=True),
        sa.Column("section", sa.String(64), nullable=True),
        sa.Column("element_type", sa.String(32), nullable=True),
        sa.Column("readable_description", sa.String(512), nullable=True),
        sa.CheckConstraint(
            "type IN ('mouse_move','click','scroll','exit_intent','visibility','mouse_summary')",
            name="ck_event_enriched_type",
        ),
    )

    # Indexes for common UI queries
    op.create_index("ix_event_enriched_session_id", "event_enriched", ["session_id"])
    op.create_index("ix_event_enriched_ts", "event_enriched", ["ts"])
    op.create_index("ix_event_enriched_type", "event_enriched", ["type"])


def downgrade() -> None:
    op.drop_index("ix_event_enriched_type", table_name="event_enriched")
    op.drop_index("ix_event_enriched_ts", table_name="event_enriched")
    op.drop_index("ix_event_enriched_session_id", table_name="event_enriched")
    op.drop_table("event_enriched")
