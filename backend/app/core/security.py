"""Security utilities for API hardening (CONV-45).

Provides request-ID injection, security headers middleware,
and input sanitization helpers.
"""

from __future__ import annotations

import re
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject security headers and request ID into every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Assign or propagate request ID for tracing
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        response = await call_next(request)

        # Tracing
        response.headers["X-Request-ID"] = request_id

        # Security headers (OWASP recommendations)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        return response


# ── Input sanitization ────────────────────────────────────────────

_UNSAFE_CHARS = re.compile(r"[<>&\"']")


def sanitize_text(value: str, max_length: int = 1000) -> str:
    """Strip dangerous characters and enforce length limit.

    Use for free-text fields that will be stored or displayed.
    Does NOT replace proper output encoding — this is defence-in-depth.
    """
    cleaned = _UNSAFE_CHARS.sub("", value)
    return cleaned[:max_length].strip()


def is_valid_uuid(value: str) -> bool:
    """Validate UUID format without raising."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
