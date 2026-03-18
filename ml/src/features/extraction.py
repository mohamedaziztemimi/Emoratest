"""Feature extraction functions for behavioral session analysis.

Computes 8 behavioral features from raw event data for ML training
and real-time prediction. Each function takes a list of event dicts
(as returned from the events table) and session metadata.

Event dict schema:
    type: str        — mouse_move | click | scroll | exit_intent | visibility
    ts: datetime     — event timestamp
    x: float | None  — mouse x coordinate
    y: float | None  — mouse y coordinate
    velocity: float | None — mouse speed
    element_id: str | None — DOM element identifier
    metadata: dict | None  — type-specific payload
"""

from __future__ import annotations

from datetime import datetime

import numpy as np


def session_duration_s(started_at: datetime, ended_at: datetime | None) -> float:
    """Total session length in seconds."""
    if ended_at is None:
        return 0.0
    return max((ended_at - started_at).total_seconds(), 0.0)


def hesitation_score(events: list[dict]) -> float:
    """Detect pauses before clicks — long gaps between mouse_move and click on same element.

    Score = mean hesitation time (seconds) across click events that had
    preceding mouse activity, capped at 1.0 and normalized by 30s max.
    """
    clicks = [e for e in events if e["type"] == "click"]
    if not clicks:
        return 0.0

    mouse_moves = [e for e in events if e["type"] == "mouse_move"]
    if not mouse_moves:
        return 0.0

    hesitations = []
    for click in clicks:
        click_ts = click["ts"]
        # Find the last mouse_move before this click
        preceding = [m for m in mouse_moves if m["ts"] < click_ts]
        if preceding:
            last_move = max(preceding, key=lambda m: m["ts"])
            gap = (click_ts - last_move["ts"]).total_seconds()
            hesitations.append(gap)

    if not hesitations:
        return 0.0

    # Normalize: 30s+ of avg hesitation = score 1.0
    max_hesitation = 30.0
    return min(float(np.mean(hesitations)) / max_hesitation, 1.0)


def price_dwell_time_s(events: list[dict]) -> float:
    """Time spent interacting with price-related elements (seconds).

    Sums durations between consecutive events on price-related elements.
    """
    price_keywords = {"price", "cost", "total", "subtotal", "amount", "fee"}

    price_events = []
    for e in events:
        eid = (e.get("element_id") or "").lower()
        if any(kw in eid for kw in price_keywords):
            price_events.append(e)

    if len(price_events) < 2:
        return 0.0

    price_events.sort(key=lambda e: e["ts"])
    total = 0.0
    for i in range(1, len(price_events)):
        gap = (price_events[i]["ts"] - price_events[i - 1]["ts"]).total_seconds()
        # Only count gaps under 30s (longer gaps = user left the element)
        if gap <= 30.0:
            total += gap

    return round(total, 2)


def rage_click_score(events: list[dict]) -> float:
    """Detect rapid repeated clicks in the same area (frustration signal).

    A rage click cluster = 3+ clicks within 2 seconds in a 50px radius.
    Score = (rage clusters) / (total click clusters), range [0, 1].
    """
    clicks = sorted(
        [e for e in events if e["type"] == "click" and e.get("x") is not None],
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


def scroll_retreat_count(events: list[dict]) -> int:
    """Count direction reversals in scrolling (down then up = indecision).

    A retreat = a scroll-up event that follows a scroll-down event.
    """
    scrolls = sorted(
        [e for e in events if e["type"] == "scroll" and e.get("metadata")],
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


def exit_intent_count(events: list[dict]) -> int:
    """Count exit intent signals (mouse leaving viewport top, tab switches)."""
    return sum(1 for e in events if e["type"] == "exit_intent")


def checkout_hesitation_s(events: list[dict]) -> float:
    """Total idle time on checkout-related elements (seconds).

    Idle = gaps > 3s between events on checkout elements, capped at 60s per gap.
    """
    checkout_keywords = {
        "checkout", "payment", "shipping", "billing", "submit", "place-order", "buy-now",
    }

    checkout_events = []
    for e in events:
        eid = (e.get("element_id") or "").lower()
        if any(kw in eid for kw in checkout_keywords):
            checkout_events.append(e)

    if len(checkout_events) < 2:
        return 0.0

    checkout_events.sort(key=lambda e: e["ts"])
    total_hesitation = 0.0

    for i in range(1, len(checkout_events)):
        gap = (checkout_events[i]["ts"] - checkout_events[i - 1]["ts"]).total_seconds()
        # Only count gaps > 3s as hesitation, cap at 60s
        if gap > 3.0:
            total_hesitation += min(gap, 60.0)

    return round(total_hesitation, 2)


def velocity_variance(events: list[dict]) -> float:
    """Variance in mouse movement speed. High variance = erratic/frustrated behavior."""
    velocities = [
        e["velocity"] for e in events
        if e["type"] == "mouse_move" and e.get("velocity") is not None
    ]

    if len(velocities) < 2:
        return 0.0

    return round(float(np.var(velocities)), 2)


def extract_features(
    events: list[dict],
    started_at: datetime,
    ended_at: datetime | None,
) -> dict[str, float | int]:
    """Compute all 8 behavioral features from raw events and session timestamps.

    Returns a dict matching the session_features table columns.
    """
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
