"""Rate limiting configuration (CONV-41).

Uses slowapi with in-memory storage for development.
In production, switch to Redis backend via REDIS_URL.

Rate tiers (per IP):
    SDK endpoints:          2000 requests/minute (high-volume event ingestion)
    Dashboard endpoints:     200 requests/minute (human-driven queries)
    Experiment endpoints:    100 requests/minute (CRUD operations)
    Intervention endpoints:  300 requests/minute (recommendation lookups)
    Merchant endpoints:       50 requests/minute (profile/key operations)
    WebSocket:                10 connections/minute (initial handshake)
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def get_rate_for_path(request: Request) -> str:
    """Determine rate limit tier based on request path."""
    path = request.url.path
    if "/dashboard/" in path:
        return "200/minute"
    if "/experiments/" in path or path.endswith("/experiments"):
        return "100/minute"
    if "/interventions/" in path or path.endswith("/interventions"):
        return "300/minute"
    if "/merchants/" in path:
        return "50/minute"
    if "/analytics/" in path:
        return "200/minute"
    if "/ws/" in path:
        return "10/minute"
    # SDK endpoints (sessions, events)
    return "2000/minute"
