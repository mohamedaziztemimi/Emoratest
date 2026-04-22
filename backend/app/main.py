"""EmoraTest API — Emotion ML + A/B Testing Platform.

FastAPI application entry point. Registers all routers, middleware,
and error handlers for production deployment.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

def is_local_network(origin: str) -> bool:
    """Check if origin is from local network."""
    if not origin:
        return False
    # Allow localhost variants
    if origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1"):
        return True
    # Allow local network IPs (10.x.x.x, 192.168.x.x, 172.16-31.x.x)
    for prefix in ["http://10.", "http://192.168.", "http://172.16.", "http://172.17.",
                   "http://172.18.", "http://172.19.", "http://172.20.", "http://172.21.",
                   "http://172.22.", "http://172.23.", "http://172.24.", "http://172.25.",
                   "http://172.26.", "http://172.27.", "http://172.28.", "http://172.29.",
                   "http://172.30.", "http://172.31."]:
        if origin.startswith(prefix):
            return True
    return False


def is_production_domain(origin: str) -> bool:
    """Check if origin is from the production domain (emoratest.com)."""
    if not origin:
        return False
    # Allow any subdomain of emoratest.com
    allowed_domains = [
        "emoratest.com",
        "www.emoratest.com",
        "api.emoratest.com",
        "dashboard.emoratest.com",
    ]
    for domain in allowed_domains:
        if origin == f"https://{domain}" or origin.endswith(f".{domain}"):
            return True
    return False

# In development mode, dynamically allow local network origins
# In production, also allow any subdomain of emoratest.com
if os.getenv("ENVIRONMENT") != "production":

    class DynamicCORSMiddleware(CORSMiddleware):
        """CORS middleware that dynamically allows local network origins in development."""

        async def preflight_handler(self, request: Request, call_next):
            origin = request.headers.get("origin")
            if origin and (is_local_network(origin) or is_production_domain(origin)):
                # Add origin to allow_origins temporarily
                if origin not in self.allow_origins:
                    self.allow_origins.append(origin)
            return await super().preflight_handler(request, call_next)

        async def simple_response(self, request: Request, call_next, response):
            origin = request.headers.get("origin")
            if origin and (is_local_network(origin) or is_production_domain(origin)):
                if origin not in self.allow_origins:
                    self.allow_origins.append(origin)
            return await super().simple_response(request, call_next, response)

    app.add_middleware(
        DynamicCORSMiddleware,
        allow_origins=default_origins + cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    # Production: also use dynamic middleware for subdomain support
    class ProductionCORSMiddleware(CORSMiddleware):
        """CORS middleware that dynamically allows production subdomains."""

        async def preflight_handler(self, request: Request, call_next):
            origin = request.headers.get("origin")
            if origin and is_production_domain(origin):
                if origin not in self.allow_origins:
                    self.allow_origins.append(origin)
            return await super().preflight_handler(request, call_next)

        async def simple_response(self, request: Request, call_next, response):
            origin = request.headers.get("origin")
            if origin and is_production_domain(origin):
                if origin not in self.allow_origins:
                    self.allow_origins.append(origin)
            return await super().simple_response(request, call_next, response)

    app.add_middleware(
        ProductionCORSMiddleware,
        allow_origins=default_origins + cors_origins,
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

# Merchant profile & key management (CONV-43)
app.include_router(merchants_router, prefix=settings.API_V1_PREFIX)

# WebSocket real-time scoring (CONV-42)
app.include_router(ws_router, prefix=settings.API_V1_PREFIX)


# ── Health check ──────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
