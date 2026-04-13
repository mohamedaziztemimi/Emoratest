"""Create feature_flags table for progressive rollouts and kill switches.

Revision ID: 006_feature_flags
Revises: 005_experiment_type_coverage
Create Date: 2026-04-12

Adds support for:
- Feature flags with progressive rollout percentages
- Kill switches for immediate disabling
- Targeting rules based on user attributes
- Multivariate variants with weights
- Environment-specific configurations
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "006_feature_flags"
down_revision: Union[str, None] = "005_experiment_type_coverage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create feature_flags table with constraints."""
    op.create_table(
        "feature_flags",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "merchant_id",
            sa.UUID(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="inactive"),
        sa.Column("rollout_percentage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("targeting_rules", sa.JSON(), nullable=True),
        sa.Column("variants", sa.JSON(), nullable=True),
        sa.Column("kill_switch", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("environments", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
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

    # Add indexes
    op.create_index("ix_feature_flags_key", "feature_flags", ["key"])
    op.create_index("ix_feature_flags_merchant_id", "feature_flags", ["merchant_id"])

    # Add constraints
    op.execute(
        """
        ALTER TABLE feature_flags
        ADD CONSTRAINT ck_feature_flags_status
        CHECK (status IN ('active','inactive','archived'))
        """
    )

    op.execute(
        """
        ALTER TABLE feature_flags
        ADD CONSTRAINT ck_feature_flags_rollout
        CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100)
        """
    )


def downgrade() -> None:
    """Drop feature_flags table."""
    op.drop_table("feature_flags")
