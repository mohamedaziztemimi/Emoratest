"""Add segments table for flexible audience segmentation.

Revision ID: 008_segments_table
Revises: 007_emotion_tables
Create Date: 2026-04-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "008_segments_table"
down_revision: Union[str, None] = "007_emotion_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create segments table for audience segmentation."""
    op.create_table(
        "segments",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "merchant_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "conditions",
            sa.JSON(),
            nullable=False,
            server_default='{"operator": "AND", "conditions": []}',
        ),
        sa.Column(
            "segment_type",
            sa.String(length=16),
            nullable=False,
            server_default="static",
        ),
        sa.Column("estimated_size", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name="fk_segments_merchant_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_segments"),
        sa.CheckConstraint(
            "segment_type IN ('static','dynamic','emotional')",
            name="ck_segments_type",
        ),
    )

    # Create indexes
    op.create_index(
        "ix_segments_merchant_id",
        "segments",
        ["merchant_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove segments table."""
    op.drop_index("ix_segments_merchant_id", table_name="segments")
    op.drop_table("segments")
