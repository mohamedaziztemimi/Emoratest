"""Feature Worker — background session processing pipeline (CONV-36).

When a session ends (or a batch of events arrives), this worker:
1. Loads all events for the session from the database
2. Runs the 8-feature extraction pipeline
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

import sqlalchemy as sa
from sqlalchemy import select, update

from app.core.database import async_session
from app.models.event import Event
from app.models.segment import Segment, SegmentType
from app.models.session import Session
from app.models.session_features import SessionFeatures
from app.services.emotion_model import EmotionModel
from app.services.targeting_service import TargetingService

logger = logging.getLogger("emoratest.feature_worker")

# Add ml/ to path so we can import feature extraction
_ML_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "ml"
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))


# ── Feature Extraction (Bundled version) ───────────────────────

def _extract_features_bundled(
    events: list[dict],
    started_at: datetime,
    ended_at: datetime | None,
) -> dict[str, float | int]:
    """Extract 8 behavioral features from events (bundled, no ML dependency)."""
    import numpy as np

    def session_duration_s(start: datetime, end: datetime | None) -> float:
        if end is None:
            return 0.0
        return max((end - start).total_seconds(), 0.0)

    def hesitation_score(evs: list[dict]) -> float:
        clicks = [e for e in evs if e["type"] == "click"]
        if not clicks:
            return 0.0

        mouse_moves = [e for e in evs if e["type"] == "mouse_move"]
        if not mouse_moves:
            return 0.0

        hesitations = []
        for click in clicks:
            click_ts = click["ts"]
            preceding = [m for m in mouse_moves if m["ts"] < click_ts]
            if preceding:
                last_move = max(preceding, key=lambda m: m["ts"])
                gap = (click_ts - last_move["ts"]).total_seconds()
                hesitations.append(gap)

        if not hesitations:
            return 0.0
        return min(float(np.mean(hesitations)) / 30.0, 1.0)

    def price_dwell_time_s(evs: list[dict]) -> float:
        price_keywords = {"price", "cost", "total", "subtotal", "amount", "fee"}
        price_events = []
        for e in evs:
            eid = (e.get("element_id") or "").lower()
            if any(kw in eid for kw in price_keywords):
                price_events.append(e)

        if len(price_events) < 2:
            return 0.0

        price_events.sort(key=lambda e: e["ts"])
        total = 0.0
        for i in range(1, len(price_events)):
            gap = (price_events[i]["ts"] - price_events[i - 1]["ts"]).total_seconds()
            if gap <= 30.0:
                total += gap
        return round(total, 2)

    def rage_click_score(evs: list[dict]) -> float:
        clicks = sorted(
            [e for e in evs if e["type"] == "click" and e.get("x") is not None],
            key=lambda e: e["ts"],
        )

        if len(clicks) < 3:
            return 0.0

        rage_clusters = 0
        total_clusters = 0
        i = 0

        while i < len(clicks):
            cluster = [clicks[i]]
            j = i + 1

            while j < len(clicks):
                time_diff = (clicks[j]["ts"] - cluster[0]["ts"]).total_seconds()
                if time_diff > 2.0:
                    break
                dx = clicks[j]["x"] - cluster[0]["x"]
                dy = clicks[j]["y"] - cluster[0]["y"]
                dist = (dx**2 + dy**2) ** 0.5
                if dist <= 50.0:
                    cluster.append(clicks[j])
                j += 1

            total_clusters += 1
            if len(cluster) >= 3:
                rage_clusters += 1
            i = max(j, i + 1)

        if total_clusters == 0:
            return 0.0
        return round(rage_clusters / total_clusters, 4)

    def scroll_retreat_count(evs: list[dict]) -> int:
        scrolls = sorted(
            [e for e in evs if e["type"] == "scroll" and e.get("metadata")],
            key=lambda e: e["ts"],
        )
        retreats = 0
        prev_direction = None

        for s in scrolls:
            meta = s["metadata"] if isinstance(s["metadata"], dict) else {}
            direction = meta.get("direction")
            if direction == "up" and prev_direction == "down":
                retreats += 1
            if direction in ("up", "down"):
                prev_direction = direction
        return retreats

    def exit_intent_count(evs: list[dict]) -> int:
        return sum(1 for e in evs if e["type"] == "exit_intent")

    def checkout_hesitation_s(evs: list[dict]) -> float:
        checkout_keywords = {
            "checkout", "payment", "shipping", "billing", "submit", "place-order", "buy-now",
        }
        checkout_events = []
        for e in evs:
            eid = (e.get("element_id") or "").lower()
            if any(kw in eid for kw in checkout_keywords):
                checkout_events.append(e)

        if len(checkout_events) < 2:
            return 0.0

        checkout_events.sort(key=lambda e: e["ts"])
        total_hesitation = 0.0

        for i in range(1, len(checkout_events)):
            gap = (checkout_events[i]["ts"] - checkout_events[i - 1]["ts"]).total_seconds()
            if gap > 3.0:
                total_hesitation += min(gap, 60.0)
        return round(total_hesitation, 2)

    def velocity_variance(evs: list[dict]) -> float:
        velocities = [
            e["velocity"] for e in evs
            if e["type"] == "mouse_move" and e.get("velocity") is not None
        ]
        if len(velocities) < 2:
            return 0.0
        return round(float(np.var(velocities)), 2)

    return {
        "hesitation_score": hesitation_score(events),
        "price_dwell_time_s": price_dwell_time_s(events),
        "rage_click_score": rage_click_score(events),
        "scroll_retreat_count": scroll_retreat_count(events),
        "exit_intent_count": exit_intent_count(events),
        "checkout_hesitation_s": checkout_hesitation_s(events),
        "velocity_variance": velocity_variance(events),
        "session_duration_s": session_duration_s(started_at, ended_at),
    }


def _extract_features_sync(
    events: list[dict],
    started_at: datetime,
    ended_at: datetime | None,
) -> dict[str, float | int]:
    """Extract features using bundled implementation (fast, no ML dependency)."""
    return _extract_features_bundled(events, started_at, ended_at)


def _adjust_emotion_scores(scores: dict, features: dict) -> dict:
    """Adjust ML emotion scores based on behavioral signals.

    When behavior signals clearly indicate an emotional state that
    the ML model missed, we boost/reduce scores accordingly.

    Works with 4 emotions: frustrated, confused, engaged, disengaged.
    """
    adjusted = dict(scores)  # copy

    rage_clicks = features.get("rage_click_score", 0)
    exit_intents = features.get("exit_intent_count", 0)
    scroll_retreats = features.get("scroll_retreat_count", 0)
    hesitation = features.get("hesitation_score", 0)
    velocity_variance = features.get("velocity_variance", 0)
    session_duration = features.get("session_duration_s", 0)

    # Rule 1: High rage clicks → boost frustrated, reduce engaged
    if rage_clicks > 0.3:
        boost = min(rage_clicks * 0.3, 0.25)
        adjusted["frustrated"] = min(1.0, adjusted.get("frustrated", 0) + boost)
        adjusted["engaged"] = max(0.0, adjusted.get("engaged", 0) - boost * 0.5)

    # Rule 2: Scroll retreats → boost confused
    if scroll_retreats >= 3:
        boost = min(scroll_retreats / 10.0, 0.2)
        adjusted["confused"] = min(1.0, adjusted.get("confused", 0) + boost)

    # Rule 3: High hesitation score → boost confused
    if hesitation > 0.5:
        boost = min(hesitation * 0.2, 0.2)
        adjusted["confused"] = min(1.0, adjusted.get("confused", 0) + boost)

    # Rule 4: Very short session → boost disengaged
    if session_duration < 10:
        boost = 0.2
        adjusted["disengaged"] = min(1.0, adjusted.get("disengaged", 0) + boost)

    # Rule 5: Very erratic movement (high velocity variance) → boost frustrated
    if velocity_variance > 500000:
        boost = min(0.15, velocity_variance / 2000000.0)
        adjusted["frustrated"] = min(1.0, adjusted.get("frustrated", 0) + boost)

    # Renormalize so scores sum to ~1.0
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: round(v / total, 4) for k, v in adjusted.items()}

    return adjusted


def _score_session_sync(
    features: dict[str, float | int],
    emotion_scores: dict[str, float] | None = None,
) -> dict | None:
    """Compute simple heuristic scores from features (no ML models required).

    Args:
        features: Behavioral features extracted from session events
        emotion_scores: Optional dict of emotion probabilities from ML model
                        e.g., {"frustration": 0.86, "delight": 0.10, ...}
    """
    try:
        # Simple heuristic scoring based on behavioral features
        # This works even without loaded ML models
        f = features

        # Base behavioral risk (existing formula, reduced to 0.7 weight)
        base_risk = (
            (f.get("rage_click_score", 0) * 0.2) +
            (min(f.get("exit_intent_count", 0) / 5.0, 1.0) * 0.2) +
            (min(f.get("scroll_retreat_count", 0) / 5.0, 1.0) * 0.15) +
            (f.get("hesitation_score", 0) * 0.15)
        )

        # Emotion-based risk adjustment (0.3 weight)
        emotion_risk = 0.0
        if emotion_scores:
            frustrated = emotion_scores.get("frustrated", 0)
            confused = emotion_scores.get("confused", 0)
            engaged = emotion_scores.get("engaged", 0)
            disengaged = emotion_scores.get("disengaged", 0)

            # Negative emotions increase risk
            negative = max(frustrated, confused, disengaged)
            # Positive emotion decreases risk
            positive = engaged

            emotion_risk = (negative * 0.3) - (positive * 0.15)
            emotion_risk = max(0.0, emotion_risk)

        risk = base_risk + emotion_risk
        risk = max(0.0, min(1.0, round(risk, 4)))

        # Friction score: based on hesitation, checkout hesitation, rage
        friction = (
            (f.get("hesitation_score", 0) * 0.3) +
            (min(f.get("checkout_hesitation_s", 0) / 60.0, 1.0) * 0.3) +
            (f.get("rage_click_score", 0) * 0.2) +
            (min(f.get("velocity_variance", 0) / 1000.0, 1.0) * 0.2)
        )
        friction = max(0.0, min(1.0, round(friction, 4)))

        # Intent label: based on overall engagement
        duration = f.get("session_duration_s", 0)
        event_count = features.get("_event_count", 0)  # passed separately

        if duration < 5 or event_count < 5:
            intent = "browsing"
        elif risk < 0.3 and friction < 0.3:
            intent = "buying"
        elif risk < 0.5:
            intent = "deciding"
        elif friction > 0.5:
            intent = "exiting"
        else:
            intent = "comparing"

        return {
            "abandonment_risk": risk,
            "friction_score": friction,
            "intent_label": intent,
            "session_score": 1.0 - risk,
            "recommended_action": "Send discount offer" if risk > 0.6 else "Show social proof",
        }
    except Exception as exc:
        logger.debug("Heuristic scoring failed: %s", exc)
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

        # 5. Run emotion model prediction FIRST (before risk scoring)
        feature_dict = {
            'hesitation_score': features.get('hesitation_score', 0),
            'price_dwell_time_s': features.get('price_dwell_time_s', 0),
            'rage_click_score': features.get('rage_click_score', 0),
            'scroll_retreat_count': features.get('scroll_retreat_count', 0),
            'exit_intent_count': features.get('exit_intent_count', 0),
            'checkout_hesitation_s': features.get('checkout_hesitation_s', 0),
            'velocity_variance': features.get('velocity_variance', 0),
            'session_duration_s': features.get('session_duration_s', 0),
        }

        # Data quality check: skip emotion prediction if insufficient data
        # Requirements: session >= 3 seconds AND >= 3 events
        session_duration = features.get('session_duration_s', 0)
        event_count = len(events)

        if session_duration < 3 or event_count < 3:
            # Mark as insufficient data for reliable emotion classification
            emotion_result = {
                'primary_emotion': 'insufficient_data',
                'confidence': 0.0,
                'all_scores': None,
                'valence': 0.5,
                'arousal': 0.5,
            }
            emotion_scores = None
            logger.debug(
                f"Session {session_id} skipped emotion classification: "
                f"duration={session_duration:.1f}s, events={event_count}"
            )
        else:
            emotion_result = EmotionModel.predict(feature_dict)
            emotion_scores = emotion_result.get('all_scores') if emotion_result else None

        # Post-processing: adjust emotion scores based on behavioral signals
        if emotion_scores:
            emotion_scores = _adjust_emotion_scores(emotion_scores, feature_dict)
            # Update emotion_result with adjusted scores
            if emotion_result:
                # Recalculate primary emotion and confidence from adjusted scores
                primary_emotion = max(emotion_scores, key=emotion_scores.get)
                confidence = emotion_scores[primary_emotion]

                # Recalculate valence/arousal based on adjusted emotions
                valence = emotion_result.get('valence', 0.5)
                arousal = emotion_result.get('arousal', 0.5)

                # Simple valence adjustment based on emotion (4-emotion system)
                negative_emotions = {'frustrated', 'confused', 'disengaged'}
                positive_emotions = {'engaged'}

                negative_weight = sum(emotion_scores.get(e, 0) for e in negative_emotions)
                positive_weight = sum(emotion_scores.get(e, 0) for e in positive_emotions)

                # Adjust valence: negative → lower, positive → higher
                valence = max(0.0, min(1.0, 0.5 + (positive_weight - negative_weight) * 0.5))

                # Adjust arousal: higher for strong emotions
                max_score = max(emotion_scores.values())
                arousal = max(0.0, min(1.0, max_score))

                emotion_result['primary_emotion'] = primary_emotion
                emotion_result['confidence'] = confidence
                emotion_result['all_scores'] = emotion_scores
                emotion_result['valence'] = round(valence, 4)
                emotion_result['arousal'] = round(arousal, 4)

        # 6. Run heuristic scoring WITH emotion data
        features_with_count = features.copy()
        features_with_count["_event_count"] = len(events)
        scoring_result = await asyncio.to_thread(
            _score_session_sync,
            features_with_count,
            emotion_scores,
        )

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

        # 7. Save emotion results to session (using the emotion_result from step 5)
        if emotion_result:
            await db.execute(
                update(Session)
                .where(Session.id == sid)
                .values(
                    primary_emotion=emotion_result['primary_emotion'],
                    emotion_confidence=emotion_result['confidence'],
                    emotion_scores=emotion_result['all_scores'],
                    valence=emotion_result['valence'],
                    arousal=emotion_result['arousal'],
                )
            )
            logger.info(
                f"Session {session_id} emotion: "
                f"{emotion_result['primary_emotion']} "
                f"({emotion_result['confidence']:.2f})"
            )
        else:
            logger.debug(f"Emotion model unavailable for {session_id}")

        await db.commit()

        # 8. Broadcast scoring update via WebSocket (CONV-42)
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


# Alias for backward compatibility
compute_session_features = process_session


# ── Segment Size Refresh Background Task ────────────────────────────


async def refresh_all_segment_sizes(merchant_id: str | None = None) -> dict:
    """Refresh estimated_size for all dynamic segments.

    Runs as a periodic background task every 6 hours.
    Samples recent users to estimate segment sizes.

    Args:
        merchant_id: Optional merchant ID to limit refresh to one merchant

    Returns:
        Summary dict with counts and errors
    """
    from sqlalchemy import select

    service = TargetingService()

    async with async_session() as db:
        # Query dynamic segments (or all segments)
        query = select(Segment).where(Segment.is_active == True)
        if merchant_id:
            query = query.where(Segment.merchant_id == merchant_id)

        # Prioritize dynamic and emotional segments
        query = query.order_by(
            # Place dynamic/emotional segments first
            sa.case(
                (Segment.segment_type == SegmentType.DYNAMIC, 0),
                (Segment.segment_type == SegmentType.EMOTIONAL, 1),
                else_=2,
            )
        )

        result = await db.execute(query)
        segments = result.scalars().all()

        if not segments:
            logger.info("No segments found for size refresh")
            return {"refreshed": 0, "errors": 0}

        logger.info("Starting segment size refresh for %d segments", len(segments))

        refreshed = 0
        errors = 0

        # Process segments in batches (5 at a time)
        batch_size = 5
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i + batch_size]
            tasks = [service.estimate_segment_size(s, db, days=30) for s in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for segment, result in zip(batch, results):
                if isinstance(result, Exception):
                    errors += 1
                    logger.warning(
                        "Failed to estimate size for segment %s: %s",
                        segment.id,
                        result,
                    )
                else:
                    # Update estimated_size in database
                    segment.estimated_size = result.estimated_size
                    refreshed += 1
                    logger.debug(
                        "Segment %s (%s): estimated %d users (confidence: %.2f)",
                        segment.id,
                        segment.name,
                        result.estimated_size,
                        result.confidence,
                    )

            # Commit batch updates
            await db.commit()

        logger.info(
            "Segment size refresh complete: %d refreshed, %d errors",
            refreshed,
            errors,
        )

        return {"refreshed": refreshed, "errors": errors}


def enqueue_segment_refresh(merchant_id: str | None = None) -> None:
    """Schedule segment size refresh as a background task.

    Args:
        merchant_id: Optional merchant ID to limit refresh to one merchant
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_safe_refresh_segments(merchant_id))
    except RuntimeError:
        logger.warning("No event loop to schedule segment refresh")


async def _safe_refresh_segments(merchant_id: str | None) -> None:
    """Wrapper that catches exceptions for segment refresh task."""
    try:
        await refresh_all_segment_sizes(merchant_id)
    except Exception:
        logger.exception("Segment size refresh failed")

