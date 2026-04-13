"""Extend experiments table for full experiment type coverage.

Revision ID: 005_experiment_type_coverage
Revises: 004_epic6_auth_gdpr
Create Date: 2026-04-12

Adds support for:
- A/B/n, MVT, split URL, multi-page, and server-side experiments
- Flicker-free delivery metadata
- Server-side flag delivery via SDK keys
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "005_experiment_type_coverage"
down_revision: Union[str, None] = "004_epic6_auth_gdpr"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new columns to experiments table."""
    # Add experiment_type enum constraint
    op.execute(
        """
        ALTER TABLE experiments
        ADD CONSTRAINT ck_experiments_type
        CHECK (experiment_type IN ('ab','mvt','split_url','multipage','server_side'))
        """
    )

    # Add n_variants constraint
    op.execute(
        """
        ALTER TABLE experiments
        ADD CONSTRAINT ck_experiments_n_variants
        CHECK (n_variants >= 2 AND n_variants <= 10)
        """
    )

    # Add new columns
    op.add_column(
        "experiments",
        sa.Column(
            "experiment_type",
            sa.String(16),
            nullable=False,
            server_default="ab",
        ),
    )
    op.add_column(
        "experiments",
        sa.Column(
            "n_variants",
            sa.Integer(),
            nullable=False,
            server_default="2",
        ),
    )
    op.add_column(
        "experiments",
        sa.Column(
            "flicker_free",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )
    op.add_column(
        "experiments",
        sa.Column("page_urls", sa.JSON(), nullable=True),
    )
    op.add_column(
        "experiments",
        sa.Column("split_url_config", sa.JSON(), nullable=True),
    )
    op.add_column(
        "experiments",
        sa.Column("server_side_key", sa.String(64), nullable=True),
    )
    op.add_column(
        "experiments",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    """Remove new columns and constraints from experiments table."""
    # Drop columns in reverse order of creation
    op.drop_column("experiments", "updated_at")
    op.drop_column("experiments", "server_side_key")
    op.drop_column("experiments", "split_url_config")
    op.drop_column("experiments", "page_urls")
    op.drop_column("experiments", "flicker_free")
    op.drop_column("experiments", "n_variants")
    op.drop_column("experiments", "experiment_type")

    # Drop constraints
    op.execute("ALTER TABLE experiments DROP CONSTRAINT IF EXISTS ck_experiments_n_variants")
    op.execute("ALTER TABLE experiments DROP CONSTRAINT IF EXISTS ck_experiments_type")
