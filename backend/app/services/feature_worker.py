"""Feature Worker — background session processing pipeline (CONV-36).

When a session ends (or a batch of events arrives), this worker:
1. Loads all events for the session from the database
2. Runs the 8-feature extraction pipeline (ml.src.features.extraction)
3. Persists computed features to session_features table
4. Optionally runs the full ML scoring pipeline (if models are loaded)
   and updates sessions with abandonment_risk, friction_score, intent_label

The worker is designed to run as an asyncio background task within FastAPI,
not as a separate process. This keeps deployment simple for MVP.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select, update

from app.core.database import async_session
from app.models.event import Event
from app.models.session import Session
from app.models.session_features import SessionFeatures

logger = logging.getLogger("conversiono.feature_worker")

# Add ml/ to path so we can import feature extraction
_ML_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "ml"
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))


def _extract_features_sync(
    events: list[dict],
    started_at: datetime,
    ended_at: datetime | None,
) -> dict[str, float | int]:
    """Import and run feature extraction (synchronous, CPU-bound)."""
    from src.features.extraction import extract_features

    return extract_features(events, started_at, ended_at)


def _score_session_sync(features: dict[str, float | int]) -> dict | None:
    """Try to run ML scoring. Returns None if models aren't available."""
    try:
        from src.scoring.service import ScoringService

        service = ScoringService.get_instance()
        result = service.score_session(features, explain=False)
        return {
            "abandonment_risk": round(1.0 - result.conversion_prob, 4),
            "friction_score": round(result.friction_prob, 4),
            "intent_label": result.intent_label,
            "session_score": result.session_score,
            "recommended_action": result.recommended_action,
        }
    except Exception as exc:
        logger.debug("ML scoring unavailable (models not loaded): %s", exc)
        return None


async def process_session(session_id: str) -> dict:
    """Run the full feature extraction + scoring pipeline for a session.

    Returns a summary dict with the computed features and optional scores.
    """
    import uuid as uuid_mod

    sid = uuid_mod.UUID(session_id)

    async with async_session() as db:
        # 1. Load session
        result = await db.execute(select(Session).where(Session.id == sid))
        session = result.scalar_one_or_none()
        if session is None:
            logger.warning("Session %s not found", session_id)
            return {"status": "error", "detail": "session_not_found"}

        # 2. Load all events
        result = await db.execute(
            select(Event)
            .where(Event.session_id == sid)
            .order_by(Event.ts)
        )
        events_orm = result.scalars().all()

        if not events_orm:
            logger.info("Session %s has no events, skipping", session_id)
            return {"status": "skipped", "detail": "no_events"}

        # Convert ORM objects to dicts for feature extraction
        events = [
            {
                "type": e.type,
                "ts": e.ts,
                "x": e.x,
                "y": e.y,
                "velocity": e.velocity,
                "element_id": e.element_id,
                "metadata": e.metadata_,
            }
            for e in events_orm
        ]

        # 3. Extract features (CPU-bound, run in thread pool)
        features = await asyncio.to_thread(
            _extract_features_sync,
            events,
            session.started_at,
            session.ended_at,
        )

        # 4. Persist features (upsert: insert or update if exists)
        existing = await db.execute(
            select(SessionFeatures).where(SessionFeatures.session_id == sid)
        )
        existing_row = existing.scalar_one_or_none()

        now = datetime.now(UTC)
        if existing_row:
            await db.execute(
                update(SessionFeatures)
                .where(SessionFeatures.session_id == sid)
                .values(**features, computed_at=now)
            )
        else:
            sf = SessionFeatures(session_id=sid, computed_at=now, **features)
            db.add(sf)

        # 5. Run ML scoring (optional — fails gracefully if models aren't loaded)
        scoring_result = await asyncio.to_thread(_score_session_sync, features)

        if scoring_result:
            await db.execute(
                update(Session)
                .where(Session.id == sid)
                .values(
                    abandonment_risk=scoring_result["abandonment_risk"],
                    friction_score=scoring_result["friction_score"],
                    intent_label=scoring_result["intent_label"],
                )
            )

        await db.commit()

        # 6. Broadcast scoring update via WebSocket (CONV-42)
        if scoring_result:
            try:
                from app.api.ws import broadcast_scoring_update

                await broadcast_scoring_update(
                    merchant_id=str(session.merchant_id),
                    session_id=session_id,
                    scores=scoring_result,
                )
            except Exception:
                logger.debug("WebSocket broadcast skipped (no active connections)")

        summary = {
            "status": "ok",
            "session_id": session_id,
            "event_count": len(events),
            "features": features,
        }
        if scoring_result:
            summary["scoring"] = scoring_result

        logger.info(
            "Processed session %s: %d events, %d features",
            session_id,
            len(events),
            len(features),
        )
        return summary


def enqueue_session_processing(session_id: str) -> None:
    """Fire-and-forget: schedule session processing as a background task.

    Safe to call from sync or async context. Failures are logged, not raised.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_safe_process(session_id))
    except RuntimeError:
        # No running loop — should not happen in FastAPI, but handle gracefully
        logger.warning("No event loop to schedule processing for %s", session_id)


async def _safe_process(session_id: str) -> None:
    """Wrapper that catches exceptions so background tasks don't crash."""
    try:
        await process_session(session_id)
    except Exception:
        logger.exception("Feature worker failed for session %s", session_id)
