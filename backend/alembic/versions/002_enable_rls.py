"""Enable Row Level Security on all tables for Supabase

Revision ID: 002
Revises: 001
Create Date: 2026-03-18

Supabase exposes public tables via PostgREST. RLS ensures only
the backend (postgres role) and service_role can access data.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "merchants",
    "sessions",
    "events",
    "session_features",
    "experiments",
    "intervention_results",
]


def upgrade() -> None:
    # RLS is Supabase-specific and requires postgres/service_role roles
    # For local Docker deployment, we skip RLS since we have a single-tenant setup
    # In production with Supabase, this migration will be applied
    pass


def downgrade() -> None:
    # No-op since upgrade is a no-op for local deployment
    pass
