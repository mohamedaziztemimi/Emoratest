"""Replace old replay system with rrweb-based recording.

Revision ID: 027_replace_replay_with_rrweb
Revises: 026_add_page_screenshot
Create Date: 2026-05-11

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "027_replace_replay_with_rrweb"
down_revision: Union[str, None] = "026_add_page_screenshot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace old mouse_path replay with rrweb DOM recording."""

    # First, delete all existing data (old format incompatible with rrweb)
    op.execute("DELETE FROM session_replay_data")

    # Drop old columns
    op.drop_column("session_replay_data", "page_screenshot")
    op.drop_column("session_replay_data", "device_pixel_ratio")
    op.drop_column("session_replay_data", "page_height")
    op.drop_column("session_replay_data", "page_width")
    op.drop_column("session_replay_data", "page_title")
    op.drop_column("session_replay_data", "mouse_path")

    # Add new rrweb columns
    op.add_column(
        "session_replay_data",
        sa.Column(
            "rrweb_events",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "session_replay_data",
        sa.Column("events_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "session_replay_data",
        sa.Column(
            "compressed_size_bytes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "session_replay_data",
        sa.Column(
            "recording_duration_ms",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    """Revert to old mouse_path replay system."""

    # Drop new rrweb columns
    op.drop_column("session_replay_data", "recording_duration_ms")
    op.drop_column("session_replay_data", "compressed_size_bytes")
    op.drop_column("session_replay_data", "events_count")
    op.drop_column("session_replay_data", "rrweb_events")

    # Add back old columns
    op.add_column(
        "session_replay_data",
        sa.Column("mouse_path", postgresql.JSON(), nullable=True),
    )
    op.add_column(
        "session_replay_data",
        sa.Column("page_title", sa.Text(), nullable=True),
    )
    op.add_column(
        "session_replay_data",
        sa.Column("page_width", sa.Integer(), nullable=True),
    )
    op.add_column(
        "session_replay_data",
        sa.Column("page_height", sa.Integer(), nullable=True),
    )
    op.add_column(
        "session_replay_data",
        sa.Column("device_pixel_ratio", sa.Float(), nullable=True),
    )
    op.add_column(
        "session_replay_data",
        sa.Column("page_screenshot", sa.Text(), nullable=True),
    )
