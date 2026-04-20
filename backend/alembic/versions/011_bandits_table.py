"""Create bandits table for multi-armed bandit experiments.

Revision ID: 011_bandits_table
Revises: 010_emotion_fields_to_sessions
Create Date: 2026-04-19

Adds support for:
- Multi-armed bandit experiments with Thompson Sampling, UCB1, ε-greedy
- Automatic variant optimization based on conversion performance
- Convergence detection and winner declaration
- Traffic allocation tracking per variant
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "011_bandits_table"
down_revision: Union[str, None] = "010_emotion_fields_to_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create bandits table with constraints."""
    op.create_table(
        "bandits",
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
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("algorithm", sa.String(32), nullable=False, server_default="thompson_sampling"),
        sa.Column("epsilon", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("exploration_factor", sa.Float(), nullable=False, server_default="2.0"),
        sa.Column("min_samples_per_arm", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("variants", sa.JSON(), nullable=True),
        sa.Column("arm_state", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("total_trials", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("converged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("winner_variant_id", sa.String(255), nullable=True),
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
    op.create_index("ix_bandits_merchant_id", "bandits", ["merchant_id"])
    op.create_index("ix_bandits_status", "bandits", ["status"])

    # Add constraints
    op.execute(
        """
        ALTER TABLE bandits
        ADD CONSTRAINT ck_bandits_algorithm
        CHECK (algorithm IN ('thompson_sampling','ucb1','epsilon_greedy'))
        """
    )

    op.execute(
        """
        ALTER TABLE bandits
        ADD CONSTRAINT ck_bandits_status
        CHECK (status IN ('active','paused','completed'))
        """
    )

    op.execute(
        """
        ALTER TABLE bandits
        ADD CONSTRAINT ck_bandits_epsilon
        CHECK (epsilon >= 0 AND epsilon <= 1)
        """
    )

    op.execute(
        """
        ALTER TABLE bandits
        ADD CONSTRAINT ck_bandits_min_samples
        CHECK (min_samples_per_arm >= 0)
        """
    )


def downgrade() -> None:
    """Drop bandits table."""
    op.drop_table("bandits")
