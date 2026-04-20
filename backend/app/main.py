"""EmoraTest API — Emotion ML + A/B Testing Platform.

FastAPI application entry point. Registers all routers, middleware,
and error handlers for production deployment.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.bandits import router as bandits_router
from app.api.dashboard import router as dashboard_router
from app.api.emotion import router as emotion_router
from app.api.experiments import router as experiments_router
from app.api.feature_flags import router as feature_flags_router
from app.api.interventions import router as interventions_router
from app.api.merchants import router as merchants_router
from app.api.sdk import router as sdk_router
from app.api.segments import router as segments_router
from app.api.webhook import router as webhook_router
from app.api.ws import router as ws_router
from app.core.audit import AuditLogMiddleware
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

# ── Static files (SDK and test page) ─────────────────────────────
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)

# Mount static directory for SDK files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ── Error handlers (CONV-45) ─────────────────────────────────────
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── Middleware (order matters: last added = first executed) ────────

# Audit logging (CONV-57)
app.add_middleware(AuditLogMiddleware)

# Security headers + request ID (CONV-45)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiter (CONV-41)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS - allow credentials for localhost (required for cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],  # Specific origins when using credentials
    allow_credentials=True,  # Required for httpOnly cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────

# Auth routes — register, login, GDPR (Epic 6)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)

# SDK routes (session + event ingestion)
app.include_router(sdk_router, prefix=settings.API_V1_PREFIX)

# Dashboard routes (session retrieval + analytics)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)

# Experiment CRUD + A/B results (CONV-38, CONV-41)
app.include_router(experiments_router, prefix=settings.API_V1_PREFIX)

# Feature flags - progressive rollouts, kill switches (Epic X2)
app.include_router(feature_flags_router, prefix=settings.API_V1_PREFIX)

# Multi-armed bandits - adaptive variant optimization (Epic X6)
app.include_router(bandits_router, prefix=settings.API_V1_PREFIX)

# Emotion classification and real-time tracking (Epic X3)
app.include_router(emotion_router, prefix=settings.API_V1_PREFIX)

# Segmentation and targeting (Epic X4)
app.include_router(segments_router, prefix=settings.API_V1_PREFIX)

# Webhooks and integrations (Epic X5)
app.include_router(webhook_router, prefix=settings.API_V1_PREFIX)

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
