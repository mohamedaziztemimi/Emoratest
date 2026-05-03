"""EmoraTest API — Emotion ML + A/B Testing Platform.

FastAPI application entry point. Registers all routers, middleware,
and error handlers for production deployment.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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

# ── Background task for alert checking ─────────────────────────────────

logger = logging.getLogger(__name__)


async def alert_checker_loop():
    """Background task that checks alert rules every 5 minutes."""
    from datetime import datetime

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.services.alert_checker import check_alerts

    alert_logger = logging.getLogger(__name__)

    # Create a sync engine for alert checking (runs in background)
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    SessionLocal = sessionmaker(bind=engine)

    while True:
        try:
            db = SessionLocal()
            try:
                fired = check_alerts(db)
                if fired > 0:
                    alert_logger.info(f"Alert checker: {fired} alert(s) fired at {datetime.utcnow()}")
                db.commit()
            finally:
                db.close()
        except Exception as e:
            alert_logger.error(f"Alert checker error: {e}", exc_info=True)

        # Sleep for 5 minutes
        await asyncio.sleep(300)


# ── Lifespan context manager ───────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Startup
    from app.services.emotion_model import EmotionModel

    # Bootstrap emotion model if artifacts don't exist
    bootstrap_emotion_model()

    # Eagerly load the emotion model and log status
    model_loaded = EmotionModel.load()
    if model_loaded:
        logger.info("ML model loaded successfully at startup — using XGBoost for predictions")
    else:
        logger.critical("ML MODEL NOT LOADED at startup — all predictions will use heuristic fallback! Check that ml/artifacts is in the Docker image.")

    # Start background alert checker
    alert_task = asyncio.create_task(alert_checker_loop())
    logger.info("Alert checker background task started")

    yield

    # Shutdown - cancel background task
    alert_task.cancel()
    try:
        await alert_task
    except asyncio.CancelledError:
        logger.info("Alert checker background task stopped")


# ── Create FastAPI app with lifespan ───────────────────────────────────

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
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

# ── CORS Middleware ─────────────────────────────────────────────────────
# SDK endpoints need to accept requests from ANY origin (customer websites).
# Dashboard endpoints are restricted to emoratest.com domains only.
# SDK uses X-SDK-Key auth, dashboard uses cookies.
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os

cors_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []


class SmartCORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware that allows any origin for SDK endpoints.

    SDK endpoints (/api/v1/sessions, /api/v1/events/*, /api/v1/sdk/*)
    accept requests from any origin since they use X-SDK-Key authentication.
    Dashboard endpoints remain restricted to emoratest.com domains.
    """

    # Allowed origins for dashboard (cookie-based auth)
    DASHBOARD_ORIGINS = [
        "https://emoratest.com",
        "https://www.emoratest.com",
        "https://api.emoratest.com",
        "https://dashboard.emoratest.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # SDK endpoints that allow any origin
    SDK_PATHS = ["/api/v1/sessions", "/api/v1/events", "/api/v1/sdk"]

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")

        # Check if this is an SDK endpoint
        is_sdk_endpoint = any(request.url.path.startswith(path) for path in self.SDK_PATHS)

        if request.method == "OPTIONS":
            # Handle preflight
            response = Response(status_code=200)
            if is_sdk_endpoint:
                # SDK: allow any origin
                response.headers["Access-Control-Allow-Origin"] = origin or "*"
            elif origin:
                # Dashboard: check allowed origins
                if self._is_allowed_dashboard_origin(origin):
                    response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Max-Age"] = "86400"
            return response

        # Pass through to actual handler
        response = await call_next(request)

        # Add CORS headers to actual response
        if is_sdk_endpoint:
            # SDK: allow any origin, no credentials needed (X-SDK-Key auth)
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
        elif origin and self._is_allowed_dashboard_origin(origin):
            # Dashboard: allow only trusted origins with credentials
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"

        return response

    def _is_allowed_dashboard_origin(self, origin: str) -> bool:
        """Check if origin is allowed for dashboard access."""
        # Check exact matches
        if origin in self.DASHBOARD_ORIGINS:
            return True
        # Check emoratest.com subdomains
        if origin.endswith(".emoratest.com") or origin.endswith("://emoratest.com"):
            return True
        # Check CORS_ORIGINS env var
        if cors_origins and origin in cors_origins:
            return True
        return False


# Use custom CORS middleware instead of CORSMiddleware
app.add_middleware(SmartCORSMiddleware)

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


@app.get("/api/v1/health/ml")
async def ml_health_check():
    """Check ML model status for monitoring and dashboard alerts."""
    from app.services.emotion_model import EmotionModel

    # Force load attempt to get current status
    EmotionModel.load()

    return {
        "model_loaded": EmotionModel.is_available(),
        "model_path": str(EmotionModel.ARTIFACTS_DIR),
        "model_type": "xgboost" if EmotionModel.is_available() else "heuristic_fallback",
        "using_fallback": EmotionModel.using_fallback(),
    }
