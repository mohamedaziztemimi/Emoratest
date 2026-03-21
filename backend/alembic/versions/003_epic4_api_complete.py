"""Epic 4 — Backend API Complete (CONV-38 to CONV-46).

Adds indexes for experiment queries, intervention aggregation,
and session cleanup performance.

Revision ID: 003
Revises: 002
Create Date: 2026-03-21
"""

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Experiment query indexes (CONV-38) ────────────────────────
    # Support listing experiments filtered by result status
    op.create_index(
        "idx_experiments_result",
        "experiments",
        ["merchant_id", "result"],
    )

    # Support listing experiments filtered by source
    op.create_index(
        "idx_experiments_source",
        "experiments",
        ["merchant_id", "source"],
    )

    # ── Intervention result indexes (CONV-39) ─────────────────────
    # Support aggregation queries by intervention_id
    op.create_index(
        "idx_intervention_results_merchant",
        "intervention_results",
        ["merchant_id", "intervention_id"],
    )

    # Support lookups by session
    op.create_index(
        "idx_intervention_results_session",
        "intervention_results",
        ["session_id"],
    )

    # Support lookups by experiment
    op.create_index(
        "idx_intervention_results_experiment",
        "intervention_results",
        ["experiment_id"],
    )

    # ── Session cleanup index (CONV-44) ───────────────────────────
    # Already exists as idx_sessions_expires from migration 001,
    # but add a covering index for the cleanup batch query
    op.create_index(
        "idx_sessions_merchant_outcome",
        "sessions",
        ["merchant_id", "outcome"],
    )

    # ── Cohort analytics indexes (CONV-40) ────────────────────────
    op.create_index(
        "idx_sessions_device_type",
        "sessions",
        ["merchant_id", "device_type"],
    )
    op.create_index(
        "idx_sessions_country_code",
        "sessions",
        ["merchant_id", "country_code"],
    )
    op.create_index(
        "idx_sessions_intent_label",
        "sessions",
        ["merchant_id", "intent_label"],
    )


def downgrade() -> None:
    op.drop_index("idx_sessions_intent_label", table_name="sessions")
    op.drop_index("idx_sessions_country_code", table_name="sessions")
    op.drop_index("idx_sessions_device_type", table_name="sessions")
    op.drop_index("idx_sessions_merchant_outcome", table_name="sessions")
    op.drop_index("idx_intervention_results_experiment", table_name="intervention_results")
    op.drop_index("idx_intervention_results_session", table_name="intervention_results")
    op.drop_index("idx_intervention_results_merchant", table_name="intervention_results")
    op.drop_index("idx_experiments_source", table_name="experiments")
    op.drop_index("idx_experiments_result", table_name="experiments")
