"""Rate limiting configuration (CONV-41).

NOTE: slowapi has been removed due to missing storage backend.
This module now provides a no-op limiter for backwards compatibility.
Critical auth endpoints use manual Redis-based rate limiting via redis_rate_limit.py.

Rate tiers (per IP) - currently disabled, will be re-enabled with Redis backend:
    SDK endpoints:          2000 requests/minute (high-volume event ingestion)
    Dashboard endpoints:     200 requests/minute (human-driven queries)
    Experiment endpoints:    100 requests/minute (CRUD operations)
    Intervention endpoints:  300 requests/minute (recommendation lookups)
    Merchant endpoints:       50 requests/minute (profile/key operations)
    WebSocket:                10 connections/minute (initial handshake)
"""

from __future__ import annotations

from dataclasses import dataclass


class DummyLimiter:
    """No-op limiter for backwards compatibility after removing slowapi."""

    def limit(self, limit_string: str):
        """Decorator that does nothing - rate limiting disabled."""

        def decorator(func):
            return func

        return decorator


# Create singleton instance
limiter = DummyLimiter()


def get_rate_for_path(request) -> str:
    """Determine rate limit tier based on request path.

    NOTE: Currently returns a default string but is not used.
    Will be re-enabled when Redis-based rate limiting is fully implemented.
    """
    return "200/minute"
