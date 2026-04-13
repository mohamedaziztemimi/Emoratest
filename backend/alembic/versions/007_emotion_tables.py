"""Create emotion_events and emotion_sessions tables.

Revision ID: 007_emotion_tables
Revises: 006_feature_flags
Create Date: 2026-04-12

Adds support for real-time emotion classification,
session aggregation, and why-analysis data.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "007_emotion_tables"
down_revision: Union[str, None] = "006_feature_flags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create emotion_events and emotion_sessions tables."""
    # Create emotion_events table
    op.create_table(
        "emotion_events",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column(
            "experiment_id",
            sa.UUID(),
            sa.ForeignKey("experiments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("variant_id", sa.UUID(), nullable=True),
        sa.Column("primary_emotion", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("valence", sa.Float(), nullable=False),
        sa.Column("arousal", sa.Float(), nullable=False),
        sa.Column("trigger_features", sa.JSON(), nullable=True),
        sa.Column("page_url", sa.String(1000), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("source", sa.String(16), nullable=False, server_default="behavioral"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create emotion_sessions table
    op.create_table(
        "emotion_sessions",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("session_id", sa.UUID(), nullable=False, unique=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column(
            "experiment_id",
            sa.UUID(),
            sa.ForeignKey("experiments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("variant_id", sa.UUID(), nullable=True),
        sa.Column("dominant_emotion", sa.String(32), nullable=True),
        sa.Column("emotion_timeline", sa.JSON(), nullable=True),
        sa.Column("frustration_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confusion_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("delight_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("converted", sa.Boolean(), nullable=True, default=None),
        sa.Column("revenue", sa.Float(), nullable=True, default=None),
        sa.Column("churn_risk", sa.Float(), nullable=True, default=None),
        sa.Column(
            "first_event_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_event_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create indexes
    op.create_index("ix_emotion_events_session_id", "emotion_events", ["session_id"])
    op.create_index("ix_emotion_events_user_id", "emotion_events", ["user_id"])
    op.create_index("ix_emotion_events_experiment_id", "emotion_events", ["experiment_id"])
    op.create_index("ix_emotion_events_timestamp", "emotion_events", ["timestamp"])

    op.create_index("ix_emotion_sessions_session_id", "emotion_sessions", ["session_id"], unique=True)
    op.create_index("ix_emotion_sessions_user_id", "emotion_sessions", ["user_id"])
    op.create_index("ix_emotion_sessions_experiment_id", "emotion_sessions", ["experiment_id"])


def downgrade() -> None:
    """Drop emotion tables."""
    op.drop_table("emotion_sessions")
    op.drop_table("emotion_events")
