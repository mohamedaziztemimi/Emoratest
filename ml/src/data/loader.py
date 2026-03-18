"""Load labeled session data from Postgres for ML training."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text

FEATURE_COLS = [
    "hesitation_score",
    "price_dwell_time_s",
    "rage_click_score",
    "scroll_retreat_count",
    "exit_intent_count",
    "checkout_hesitation_s",
    "velocity_variance",
    "session_duration_s",
]


def _make_engine(database_url: str):
    sync_url = database_url.replace("+asyncpg", "").replace("+aiopg", "")
    return create_engine(sync_url)


def load_training_data(database_url: str) -> pd.DataFrame:
    """Load session_features joined with session outcome labels.

    Returns a DataFrame with 8 feature columns + 'label' (1=purchase, 0=abandon).
    """
    engine = _make_engine(database_url)

    query = text("""
        SELECT
            sf.hesitation_score,
            sf.price_dwell_time_s,
            sf.rage_click_score,
            sf.scroll_retreat_count,
            sf.exit_intent_count,
            sf.checkout_hesitation_s,
            sf.velocity_variance,
            sf.session_duration_s,
            CASE WHEN s.outcome = 'purchase' THEN 1 ELSE 0 END AS label
        FROM session_features sf
        JOIN sessions s ON s.id = sf.session_id
        WHERE s.outcome IN ('purchase', 'abandon')
    """)

    df = pd.read_sql(query, engine)
    engine.dispose()
    return df


def load_intent_data(database_url: str) -> pd.DataFrame:
    """Load session_features joined with intent labels.

    Returns a DataFrame with 8 feature columns + 'intent_label'.
    """
    engine = _make_engine(database_url)

    query = text("""
        SELECT
            sf.hesitation_score,
            sf.price_dwell_time_s,
            sf.rage_click_score,
            sf.scroll_retreat_count,
            sf.exit_intent_count,
            sf.checkout_hesitation_s,
            sf.velocity_variance,
            sf.session_duration_s,
            s.intent_label
        FROM session_features sf
        JOIN sessions s ON s.id = sf.session_id
        WHERE s.intent_label IS NOT NULL
    """)

    df = pd.read_sql(query, engine)
    engine.dispose()
    return df


def load_friction_data(database_url: str, threshold: float = 0.5) -> pd.DataFrame:
    """Load session_features with friction labels.

    Returns a DataFrame with 8 feature columns + 'label' (1=high friction, 0=low).
    Sessions with friction_score >= threshold are labeled as high friction.
    """
    engine = _make_engine(database_url)

    query = text("""
        SELECT
            sf.hesitation_score,
            sf.price_dwell_time_s,
            sf.rage_click_score,
            sf.scroll_retreat_count,
            sf.exit_intent_count,
            sf.checkout_hesitation_s,
            sf.velocity_variance,
            sf.session_duration_s,
            s.friction_score
        FROM session_features sf
        JOIN sessions s ON s.id = sf.session_id
        WHERE s.friction_score IS NOT NULL
    """)

    df = pd.read_sql(query, engine)
    engine.dispose()

    df["label"] = (df["friction_score"] >= threshold).astype(int)
    df = df.drop(columns=["friction_score"])
    return df
