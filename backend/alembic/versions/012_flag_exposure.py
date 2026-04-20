"""Add flag_exposures table for conversion tracking.

Revision ID: 012_flag_exposure
Revises: 011_bandits_table
Create Date: 2026-04-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012_flag_exposure"
down_revision: Union[str, None] = "011_bandits_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the flag_exposures table."""
    # Table already created manually, skip
    pass


def downgrade() -> None:
    """Drop the flag_exposures table."""
    op.drop_table("flag_exposures")
