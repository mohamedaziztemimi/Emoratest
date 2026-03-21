"""Conversiono API — AI behavioral intelligence for e-commerce.

FastAPI application entry point. Registers all routers, middleware,
and error handlers for production deployment.
"""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.analytics import router as analytics_router
from app.api.dashboard import router as dashboard_router
from app.api.experiments import router as experiments_router
from app.api.interventions import router as interventions_router
from app.api.merchants import router as merchants_router
from app.api.sdk import router as sdk_router
from app.api.ws import router as ws_router
from app.core.config import settings
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.rate_limit import limiter
from app.core.security import SecurityHeadersMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# ── Error handlers (CONV-45) ─────────────────────────────────────
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── Middleware (order matters: last added = first executed) ────────

# Security headers + request ID (CONV-45)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiter (CONV-41)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────

# SDK routes (session + event ingestion)
app.include_router(sdk_router, prefix=settings.API_V1_PREFIX)

# Dashboard routes (session retrieval + analytics)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)

# Experiment CRUD + A/B results (CONV-38, CONV-41)
app.include_router(experiments_router, prefix=settings.API_V1_PREFIX)

# Intervention recommendations + tracking (CONV-39)
app.include_router(interventions_router, prefix=settings.API_V1_PREFIX)

# Cohort & segment analytics (CONV-40)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)

# Merchant profile & key management (CONV-43)
app.include_router(merchants_router, prefix=settings.API_V1_PREFIX)

# WebSocket real-time scoring (CONV-42)
app.include_router(ws_router, prefix=settings.API_V1_PREFIX)


# ── Health check ──────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
