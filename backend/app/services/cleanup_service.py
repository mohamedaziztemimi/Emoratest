"""Session Cleanup & Data Retention Service (CONV-44).

Provides automated cleanup of expired sessions and their associated data.
Designed to run as a periodic background task within FastAPI.

Retention policy:
- Sessions older than expires_at are hard-deleted (cascade to events, features)
- Default TTL is 90 days (set at session creation)
- Cleanup runs in batches to avoid long-running transactions
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import delete, func, select

from app.core.database import async_session
from app.models.event import Event
from app.models.intervention_result import InterventionResult
from app.models.session import Session
from app.models.session_features import SessionFeatures

logger = logging.getLogger("emoratest.cleanup")

# Maximum sessions to delete per cleanup run (prevent long transactions)
BATCH_SIZE = 500


async def cleanup_expired_sessions() -> dict:
    """Delete sessions past their expires_at timestamp.

    Returns a summary of what was cleaned up.
    """
    now = datetime.now(UTC)
    total_deleted = 0
    total_events_deleted = 0
    total_features_deleted = 0
    total_interventions_deleted = 0

    async with async_session() as db:
        while True:
            # Find expired session IDs in batches
            expired_query = (
                select(Session.id)
                .where(Session.expires_at <= now)
                .limit(BATCH_SIZE)
            )
            result = await db.execute(expired_query)
            expired_ids = [row[0] for row in result.all()]

            if not expired_ids:
                break

            # Delete related records first (respect FK constraints)
            # Events
            event_result = await db.execute(
                delete(Event).where(Event.session_id.in_(expired_ids))
            )
            total_events_deleted += event_result.rowcount

            # Session features
            feat_result = await db.execute(
                delete(SessionFeatures).where(SessionFeatures.session_id.in_(expired_ids))
            )
            total_features_deleted += feat_result.rowcount

            # Intervention results
            intv_result = await db.execute(
                delete(InterventionResult).where(InterventionResult.session_id.in_(expired_ids))
            )
            total_interventions_deleted += intv_result.rowcount

            # Delete sessions themselves
            sess_result = await db.execute(
                delete(Session).where(Session.id.in_(expired_ids))
            )
            total_deleted += sess_result.rowcount

            await db.commit()

            logger.info("Cleanup batch: deleted %d sessions", len(expired_ids))

        # Count remaining sessions for summary
        count_result = await db.execute(select(func.count()).select_from(Session))
        remaining = count_result.scalar() or 0

    summary = {
        "status": "completed",
        "expired_sessions_deleted": total_deleted,
        "events_deleted": total_events_deleted,
        "features_deleted": total_features_deleted,
        "interventions_deleted": total_interventions_deleted,
        "remaining_sessions": remaining,
        "run_at": now.isoformat(),
    }
    logger.info("Cleanup completed: %s", summary)
    return summary


async def get_retention_stats() -> dict:
    """Get data retention statistics for the merchant dashboard."""
    now = datetime.now(UTC)

    async with async_session() as db:
        # Total sessions
        total_result = await db.execute(select(func.count()).select_from(Session))
        total = total_result.scalar() or 0

        # Expired (pending cleanup)
        expired_result = await db.execute(
            select(func.count())
            .select_from(Session)
            .where(Session.expires_at <= now)
        )
        expired = expired_result.scalar() or 0

        # Expiring in next 7 days
        from datetime import timedelta

        expiring_soon_result = await db.execute(
            select(func.count())
            .select_from(Session)
            .where(
                Session.expires_at > now,
                Session.expires_at <= now + timedelta(days=7),
            )
        )
        expiring_soon = expiring_soon_result.scalar() or 0

        # Total events
        events_result = await db.execute(select(func.count()).select_from(Event))
        total_events = events_result.scalar() or 0

    return {
        "total_sessions": total,
        "expired_sessions": expired,
        "expiring_within_7_days": expiring_soon,
        "total_events": total_events,
        "retention_days": 90,
        "checked_at": now.isoformat(),
    }
