"""Add page_screenshot column to session_replay_data.

Revision ID: 026_add_page_screenshot
Revises: 025_session_replay_data
Create Date: 2026-05-09

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "026_add_page_screenshot"
down_revision: Union[str, None] = "025_session_replay_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add page_screenshot column to session_replay_data table."""
    op.add_column(
        "session_replay_data",
        sa.Column("page_screenshot", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove page_screenshot column from session_replay_data table."""
    op.drop_column("session_replay_data", "page_screenshot")
