"""Epic 6 — Add password auth, GDPR consent, onboarding fields to merchants.

Revision ID: 004
Revises: 003_epic4_api_complete
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("merchants", sa.Column("password_hash", sa.String(128), nullable=True))
    op.add_column(
        "merchants",
        sa.Column("gdpr_consent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "merchants",
        sa.Column("gdpr_consent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "merchants",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("merchants", "onboarding_completed")
    op.drop_column("merchants", "gdpr_consent_at")
    op.drop_column("merchants", "gdpr_consent")
    op.drop_column("merchants", "password_hash")
