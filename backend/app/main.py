"""EmoraTest API — Emotion ML + A/B Testing Platform.

FastAPI application entry point. Registers all routers, middleware,
and error handlers for production deployment.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.alerts import router as alerts_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.bandits import router as bandits_router
from app.api.dashboard import router as dashboard_router
from app.api.diagnosis import router as diagnosis_router
from app.api.emotion import router as emotion_router
from app.api.experiments import router as experiments_router
from app.api.feature_flags import router as feature_flags_router
from app.api.interventions import router as interventions_router
from app.api.merchants import router as merchants_router
from app.api.pages import router as pages_router
from app.api.sdk import router as sdk_router
from app.api.segments import router as segments_router
from app.api.waitlist import router as waitlist_router
from app.api.webhook import router as webhook_router
from app.api.ws import router as ws_router
from app.core.audit import AuditLogMiddleware
from app.core.config import settings
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.security import SecurityHeadersMiddleware

# Import emotion model bootstrap for ML pipeline initialization
from app.services.emotion_model_bootstrap import bootstrap_emotion_model

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)


# ── Startup events ────────────────────────────────────────────────────


@app.on_event("startup")
async def startup_event():
    """Initialize ML models on startup."""
    # Bootstrap emotion model if artifacts don't exist
    bootstrap_emotion_model()

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

# CORS - allow credentials for localhost, local network, and production
# Use environment variable or allow all origins in development
import os

cors_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []

if os.getenv("ENVIRONMENT") == "production":
    # In production, use configured origins
    # Include all subdomains for cross-domain support
    default_origins = [
        "https://emoratest.com",
        "https://www.emoratest.com",
        "https://api.emoratest.com",
        "https://dashboard.emoratest.com",
    ]
elif not cors_origins:
    # In development, allow localhost and local network IPs
    default_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        # Allow common local network IP ranges (will be validated dynamically)
        "http://10.*",
        "http://192.168.*",
        "http://172.16.*",
        "http://172.17.*",
        "http://172.18.*",
        "http://172.19.*",
        "http://172.20.*",
        "http://172.21.*",
        "http://172.22.*",
        "http://172.23.*",
        "http://172.24.*",
        "http://172.25.*",
        "http://172.26.*",
        "http://172.27.*",
        "http://172.28.*",
        "http://172.29.*",
        "http://172.30.*",
        "http://172.31.*",
    ]
else:
    default_origins = []

# Use standard CORSMiddleware - wildcard for development, specific domains for production
# The allow_origin_regex parameter handles dynamic subdomain matching
if os.getenv("ENVIRONMENT") == "production":
    # Production: allow all emoratest.com subdomains via regex
    allow_origin_regex = r"https://([a-z0-9-]+\.)*emoratest\.com"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=default_origins + cors_origins,
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    # Development: allow localhost and local network via regex
    allow_origin_regex = r"https?://(localhost|127\.0\.0\.1|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=default_origins + cors_origins,
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

# ── Payload size limit middleware ────────────────────────────────────

MAX_PAYLOAD_SIZE = 1_048_576  # 1MB


@app.middleware("http")
async def limit_payload_size(request: Request, call_next):
    """Reject requests with payload larger than 1MB to prevent DoS attacks."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
            if size > MAX_PAYLOAD_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Payload too large. Maximum size is {MAX_PAYLOAD_SIZE // 1024}KB."},
                )
        except ValueError:
            pass
    return await call_next(request)

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

# Diagnosis — behavioral signal to actionable insight conversion
app.include_router(diagnosis_router, prefix=settings.API_V1_PREFIX)

# Merchant profile & key management (CONV-43)
app.include_router(merchants_router, prefix=settings.API_V1_PREFIX)

# WebSocket real-time scoring (CONV-42)
app.include_router(ws_router, prefix=settings.API_V1_PREFIX)

# Alerts — emotion spike notifications (retention feature)
app.include_router(alerts_router, prefix=settings.API_V1_PREFIX)

# Pages — page-level emotion insights
app.include_router(pages_router)

# Waitlist — for users interested in paid plans
app.include_router(waitlist_router, prefix=settings.API_V1_PREFIX)


# ── Health check ──────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
