"""Initial schema — merchants, sessions, events, session_features, experiments, intervention_results

Revision ID: 001
Revises:
Create Date: 2026-03-17

All DDL from Master Technical Document Section 4.1 + indexes from Section 4.2.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── merchants ──────────────────────────────────────────────────
    op.create_table(
        "merchants",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("shop_domain", sa.String(255), unique=True, nullable=False),
        sa.Column("sdk_key_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("plan", sa.String(32), nullable=False, server_default=sa.text("'trial'")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "plan IN ('trial','starter','growth','scale','enterprise')",
            name="ck_merchants_plan",
        ),
    )

    # ── sessions ────────────────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_url", sa.Text, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("outcome", sa.String(16), nullable=False, server_default="unknown"),
        sa.Column("abandonment_risk", sa.Float),
        sa.Column("friction_score", sa.Float),
        sa.Column("intent_label", sa.String(32)),
        sa.Column("country_code", sa.CHAR(2)),
        sa.Column("device_type", sa.String(16)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("outcome IN ('purchase','abandon','unknown')", name="ck_sessions_outcome"),
        sa.CheckConstraint("abandonment_risk BETWEEN 0 AND 1", name="ck_sessions_abandonment_risk"),
        sa.CheckConstraint("friction_score BETWEEN 0 AND 1", name="ck_sessions_friction_score"),
    )

    # ── events (HIGH VOLUME) ──────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("x", sa.Float),
        sa.Column("y", sa.Float),
        sa.Column("velocity", sa.Float),
        sa.Column("element_id", sa.String(128)),
        sa.Column("metadata", JSONB),
        sa.CheckConstraint(
            "type IN ('mouse_move','click','scroll','exit_intent','visibility')",
            name="ck_events_type",
        ),
    )

    # ── session_features ────────────────────────────────────────────
    op.create_table(
        "session_features",
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("hesitation_score", sa.Float),
        sa.Column("price_dwell_time_s", sa.Float),
        sa.Column("rage_click_score", sa.Float),
        sa.Column("scroll_retreat_count", sa.Integer),
        sa.Column("exit_intent_count", sa.Integer),
        sa.Column("checkout_hesitation_s", sa.Float),
        sa.Column("velocity_variance", sa.Float),
        sa.Column("session_duration_s", sa.Float),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ── experiments ─────────────────────────────────────────────────
    op.create_table(
        "experiments",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("merchant_id", UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("hypothesis", sa.Text),
        sa.Column("page_element", sa.String(128)),
        sa.Column("friction_type", sa.String(64)),
        sa.Column("variant_a", sa.Text),
        sa.Column("variant_b", sa.Text),
        sa.Column("result", sa.String(16)),
        sa.Column("conversion_delta", sa.Float),
        sa.Column("sample_size", sa.Integer),
        sa.Column("ran_at", sa.Date),
        sa.Column("source", sa.String(32), server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "result IN ('a_wins','b_wins','no_diff','inconclusive')",
            name="ck_experiments_result",
        ),
    )

    # ── intervention_results ────────────────────────────────────────
    op.create_table(
        "intervention_results",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("merchant_id", UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("experiment_id", UUID(as_uuid=True), sa.ForeignKey("experiments.id")),
        sa.Column("intervention_id", sa.String(16), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id")),
        sa.Column("outcome", sa.String(16)),
        sa.Column("conversion_delta", sa.Float),
    )

    # ── Indexes (Section 4.2) ──────────────────────────────────────
    # Sessions: merchant dashboard queries
    op.create_index("idx_sessions_merchant_date", "sessions", ["merchant_id", sa.text("started_at DESC")])
    op.create_index("idx_sessions_expires", "sessions", ["expires_at"])
    op.create_index("idx_sessions_risk", "sessions", ["merchant_id", sa.text("abandonment_risk DESC")])

    # Events: session detail and feature extraction
    op.create_index("idx_events_session_ts", "events", ["session_id", "ts"])

    # Experiments: merchant history and semantic search
    op.create_index("idx_experiments_merchant", "experiments", ["merchant_id", sa.text("ran_at DESC")])
    op.create_index("idx_experiments_friction", "experiments", ["merchant_id", "friction_type"])

    # Note: pgvector extension moved to V2 (Epic 9 - Semantic Search)
    # This migration now supports V1 MVP without external dependencies


def downgrade() -> None:
    op.drop_index("idx_experiments_embed", "experiments")
    op.drop_index("idx_experiments_friction", "experiments")
    op.drop_index("idx_experiments_merchant", "experiments")
    op.drop_index("idx_events_session_ts", "events")
    op.drop_index("idx_sessions_risk", "sessions")
    op.drop_index("idx_sessions_expires", "sessions")
    op.drop_index("idx_sessions_merchant_date", "sessions")

    op.drop_table("intervention_results")
    op.drop_table("experiments")
    op.drop_table("session_features")
    op.drop_table("events")
    op.drop_table("sessions")
    op.drop_table("merchants")
