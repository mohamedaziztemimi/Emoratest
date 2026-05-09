"""Add session_replay_data table for emotion replay feature.

Revision ID: 025_session_replay_data
Revises: 024_fix_session_limits_and_add_unlimited
Create Date: 2026-05-08

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "025_session_replay_data"
down_revision: Union[str, None] = "024_fix_limits_add_unlimited"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create session_replay_data table."""
    op.create_table(
        "session_replay_data",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.UUID(),
            nullable=False,
        ),
        # Mouse path: array of {x, y, timestamp, viewport_width, viewport_height, scroll_x, scroll_y}
        # and page_change events: {type: "page_change", url, timestamp}
        sa.Column("mouse_path", sa.JSON(), nullable=True),
        # Page metadata captured at session start
        sa.Column("page_url", sa.Text(), nullable=True),
        sa.Column("page_title", sa.Text(), nullable=True),
        sa.Column("page_width", sa.Integer(), nullable=True),
        sa.Column("page_height", sa.Integer(), nullable=True),
        sa.Column("device_pixel_ratio", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name="fk_session_replay_data_session_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_session_replay_data"),
        # Unique constraint on session_id (one replay record per session)
        sa.UniqueConstraint("session_id", name="uq_session_replay_data_session_id"),
    )

    # Create index on session_id for fast lookups
    op.create_index(
        "ix_session_replay_data_session_id",
        "session_replay_data",
        ["session_id"],
        unique=True,  # Already enforced by unique constraint, but index helps queries
    )


def downgrade() -> None:
    """Remove session_replay_data table."""
    op.drop_index("ix_session_replay_data_session_id", table_name="session_replay_data")
    op.drop_table("session_replay_data")
