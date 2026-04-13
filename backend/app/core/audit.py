"""Audit logging middleware (Epic 6 — CONV-57).

Logs all mutating API requests (POST, PUT, PATCH, DELETE) with
merchant identity, request path, and timestamp for compliance.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("emoratest.audit")

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if request.method in MUTATING_METHODS:
            request_id = getattr(request.state, "request_id", "unknown")
            merchant_id = getattr(request.state, "merchant_id", "anonymous")
            logger.info(
                "AUDIT | %s | %s %s | merchant=%s | status=%d | request_id=%s",
                datetime.now(UTC).isoformat(),
                request.method,
                request.url.path,
                merchant_id,
                response.status_code,
                request_id,
            )

        return response
