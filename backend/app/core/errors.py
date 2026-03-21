"""Structured error handling for production API (CONV-45).

Provides consistent error response format across all endpoints,
masking internal details in production while logging full context.
All error responses include the X-Request-ID for correlation.
"""

from __future__ import annotations

import logging
import traceback
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("conversiono.errors")


class ErrorResponse(BaseModel):
    """Consistent error envelope returned to clients."""

    error: str
    detail: str
    status_code: int
    request_id: str | None = None


def _get_request_id(request: Request) -> str | None:
    """Extract request ID from state (set by SecurityHeadersMiddleware) or header."""
    return getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException with structured JSON response."""
    request_id = _get_request_id(request)
    logger.warning(
        "HTTP %d on %s %s [request_id=%s]: %s",
        exc.status_code, request.method, request.url.path, request_id, exc.detail,
    )
    body = ErrorResponse(
        error=_status_phrase(exc.status_code),
        detail=str(exc.detail),
        status_code=exc.status_code,
        request_id=request_id,
    )
    headers = {"X-Request-ID": request_id} if request_id else {}
    return JSONResponse(status_code=exc.status_code, content=body.model_dump(), headers=headers)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors — return 422 with field-level detail."""
    request_id = _get_request_id(request)
    errors = exc.errors()
    # Sanitize: only expose field name + message, never raw input values
    safe_errors = [
        {"field": " -> ".join(str(loc) for loc in e.get("loc", [])), "message": e.get("msg", "")}
        for e in errors
    ]
    logger.warning(
        "Validation error on %s %s [request_id=%s]: %d field errors",
        request.method, request.url.path, request_id, len(safe_errors),
    )
    body = {
        "error": "Validation Error",
        "detail": safe_errors,
        "status_code": 422,
        "request_id": request_id,
    }
    headers = {"X-Request-ID": request_id} if request_id else {}
    return JSONResponse(status_code=422, content=body, headers=headers)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions — log full trace, return safe 500."""
    request_id = _get_request_id(request)
    logger.error(
        "Unhandled exception on %s %s [request_id=%s]: %s\n%s",
        request.method,
        request.url.path,
        request_id,
        exc,
        traceback.format_exc(),
    )
    body = ErrorResponse(
        error="Internal Server Error",
        detail="An unexpected error occurred. Please try again later.",
        status_code=500,
        request_id=request_id,
    )
    headers = {"X-Request-ID": request_id} if request_id else {}
    return JSONResponse(status_code=500, content=body.model_dump(), headers=headers)


def _status_phrase(code: int) -> str:
    """Return HTTP status phrase for common codes."""
    phrases: dict[int, str] = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }
    return phrases.get(code, "Error")
