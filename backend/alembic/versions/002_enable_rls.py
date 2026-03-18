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
    for table in TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f'CREATE POLICY "{table}_backend_all" ON public.{table} '
            f"FOR ALL TO postgres USING (true) WITH CHECK (true)"
        )
        op.execute(
            f'CREATE POLICY "{table}_service_all" ON public.{table} '
            f"FOR ALL TO service_role USING (true) WITH CHECK (true)"
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(f'DROP POLICY IF EXISTS "{table}_service_all" ON public.{table}')
        op.execute(f'DROP POLICY IF EXISTS "{table}_backend_all" ON public.{table}')
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")
