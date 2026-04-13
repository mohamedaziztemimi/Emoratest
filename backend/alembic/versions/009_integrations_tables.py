"""Add integrations and webhook_logs tables for third-party connections.

Revision ID: 009_integrations_tables
Revises: 008_segments_table
Create Date: 2026-04-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "009_integrations_tables"
down_revision: Union[str, None] = "008_segments_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create integrations and webhook_logs tables."""
    # Create integrations table
    op.create_table(
        "integrations",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "integration_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column(
            "events",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
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
            ["workspace_id"],
            ["merchants.id"],
            name="fk_integrations_workspace_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_integrations"),
    )

    # Create webhook_logs table
    op.create_table(
        "webhook_logs",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "integration_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["integration_id"],
            ["integrations.id"],
            name="fk_webhook_logs_integration_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_webhook_logs"),
    )

    # Create indexes
    op.create_index(
        "ix_integrations_workspace_id",
        "integrations",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_logs_integration_id",
        "webhook_logs",
        ["integration_id"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_logs_created_at",
        "webhook_logs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove integrations and webhook_logs tables."""
    op.drop_index("ix_webhook_logs_created_at", table_name="webhook_logs")
    op.drop_index("ix_webhook_logs_integration_id", table_name="webhook_logs")
    op.drop_index("ix_integrations_workspace_id", table_name="integrations")
    op.drop_table("webhook_logs")
    op.drop_table("integrations")
