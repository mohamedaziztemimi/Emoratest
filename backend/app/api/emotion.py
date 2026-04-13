"""Emotion API - ingestion, classification, why-analysis, and alerts.

REST endpoints and WebSocket for real-time emotion tracking.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.emotion_event import EmotionSession
from app.services.emotion_service import (
    EmotionResult,
    EmotionService,
    ExperimentROI,
    WhyAnalysis,
)
from app.services.sdk_auth import authenticate_sdk_key, get_sdk_key_header

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/emotion", tags=["emotion"])
service = EmotionService()


# ── Request/Response Schemas ────────────────────────────────────────


class EmotionEventRequest(BaseModel):
    """Request to ingest emotion events."""

    session_id: str = Field(..., description="Session identifier")
    user_id: str | None = Field(None, description="User identifier")
    events: list[dict] = Field(..., min_length=1, max_length=1000, description="Raw event stream")
    experiment_id: str | None = Field(None, description="Associated experiment ID")
    variant_id: str | None = Field(None, description="Associated variant ID")
    page_url: str = Field(default="", max_length=1000)


class EmotionEventResponse(BaseModel):
    """Response from emotion event ingestion."""

    session_id: str
    events_processed: int
    primary_emotion: str
    confidence: float
    valence: float
    arousal: float


class SessionEmotionSummary(BaseModel):
    """Summary of emotions for a session."""

    session_id: str
    user_id: str | None = None
    dominant_emotion: str | None = None
    emotion_timeline: list[dict] | None = None
    frustration_score: float = 0.0
    confusion_score: float = 0.0
    delight_score: float = 0.0
    converted: bool | None = None
    churn_risk: float | None = None


class WhyAnalysisResponse(BaseModel):
    """Why-analysis report response."""

    experiment_id: str
    top_emotion_dropoffs: list[dict]
    emotion_to_conversion_correlation: dict[str, float]
    frustration_funnel_map: dict[str, float]
    revenue_by_emotion: dict[str, float]
    total_sessions: int
    total_converted: int
    total_revenue: float
    generated_at: str


class ExperimentPrioritizationResponse(BaseModel):
    """Experiment ROI ranking response."""

    experiments: list[dict]
    generated_at: str


class ChurnRiskResponse(BaseModel):
    """Churn risk prediction response."""

    session_id: str
    churn_risk: float
    calculated_at: str


class FrustrationSpikeResponse(BaseModel):
    """Frustration spike detection response."""

    experiment_id: str
    spike_detected: bool
    window_minutes: int
    checked_at: str


# ── WebSocket Manager ────────────────────────────────────────────────


class ConnectionManager:
    """Manages WebSocket connections for real-time emotion updates."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and store WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, session_id: str):
        """Remove WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")

    async def send_emotion_update(self, session_id: str, emotion_data: dict):
        """Send emotion update to connected client."""
        if session_id in self.active_connections:
            ws = self.active_connections[session_id]
            await ws.send_json(emotion_data)


ws_manager = ConnectionManager()


# ── ENDPOINTS: Event Ingestion ───────────────────────────────────


@router.post(
    "/events",
    response_model=EmotionEventResponse,
    summary="Ingest and classify emotion events",
)
@limiter.limit("100/minute")
async def ingest_emotion_events(
    request: Request,
    body: EmotionEventRequest,
    db: Any = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Ingest raw behavioral events and classify emotions.

    Immediately returns classification result while persisting
    events asynchronously.
    """
    await authenticate_sdk_key(db, sdk_key_hash)

    # Validate session exists (would check Session table)
    # For now, proceed

    # Classify events
    result: EmotionResult = service.ingest_events(
        session_id=body.session_id,
        raw_events=body.events,
        experiment_id=body.experiment_id,
        variant_id=body.variant_id,
        db=db,
        user_id=body.user_id,
        page_url=body.page_url,
    )

    return EmotionEventResponse(
        session_id=body.session_id,
        events_processed=len(body.events),
        primary_emotion=result.primary_emotion,
        confidence=result.confidence,
        valence=result.valence,
        arousal=result.arousal,
    )


# ── ENDPOINTS: Session Summary ───────────────────────────────────


@router.get(
    "/session/{session_id}",
    response_model=SessionEmotionSummary,
    summary="Get session emotion summary",
)
@limiter.limit("200/minute")
async def get_session_emotion_summary(
    request: Request,
    session_id: str,
    db: Any = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Get aggregated emotion summary for a session."""
    await authenticate_sdk_key(db, sdk_key_hash)

    # Query emotion session
    async_db: AsyncSession = db
    result = await async_db.execute(
        select(EmotionSession).where(EmotionSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail=f"Emotion session not found: {session_id}")

    return SessionEmotionSummary(
        session_id=str(session.session_id),
        user_id=str(session.user_id) if session.user_id else None,
        dominant_emotion=session.dominant_emotion,
        emotion_timeline=session.emotion_timeline,
        frustration_score=session.frustration_score,
        confusion_score=session.confusion_score,
        delight_score=session.delight_score,
        converted=session.converted,
        churn_risk=session.churn_risk,
    )


# ── ENDPOINTS: Why Analysis ─────────────────────────────────────


@router.get(
    "/experiments/{experiment_id}/why-analysis",
    response_model=WhyAnalysisResponse,
    summary="Get why-analysis report",
)
@limiter.limit("100/minute")
async def get_why_analysis(
    request: Request,
    experiment_id: str,
    variant_id: str | None = Query(None, description="Filter by variant"),
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    db: Any = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Generate why-analysis linking emotions to behaviors and revenue."""
    await authenticate_sdk_key(db, sdk_key_hash)

    # Run why-analysis
    analysis: WhyAnalysis = await service.get_why_analysis(
        experiment_id=experiment_id,
        variant_id=variant_id,
        days=days,
        db=db,
    )

    return WhyAnalysisResponse(
        experiment_id=experiment_id,
        top_emotion_dropoffs=[
            {
                "emotion": drop.emotion,
                "drop_off_count": drop.drop_off_count,
                "drop_off_percentage": drop.drop_off_percentage,
                "avg_time_to_drop_off": drop.avg_time_to_drop_off,
            }
            for drop in analysis.top_emotion_dropoffs
        ],
        emotion_to_conversion_correlation=analysis.emotion_to_conversion_correlation,
        frustration_funnel_map=analysis.frustration_funnel_map,
        revenue_by_emotion=analysis.revenue_by_emotion,
        total_sessions=analysis.total_sessions,
        total_converted=analysis.total_converted,
        total_revenue=analysis.total_revenue,
        generated_at=datetime.now(UTC).isoformat(),
    )


# ── ENDPOINTS: Experiment Prioritization ─────────────────────────


@router.get(
    "/experiments/prioritization",
    response_model=ExperimentPrioritizationResponse,
    summary="Get experiment ROI ranking",
)
@limiter.limit("100/minute")
async def get_experiment_prioritization(
    request: Request,
    experiment_ids: str = Query(..., description="Comma-separated experiment IDs"),
    db: Any = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Rank experiments by emotional ROI for prioritization.

    Returns sorted list with ROI scores, primary emotion opportunities,
    and estimated conversion lift.
    """
    await authenticate_sdk_key(db, sdk_key_hash)

    # Parse experiment IDs
    exp_id_list = [e.strip() for e in experiment_ids.split(",")]

    # Get ROI ranking
    rankings: list[ExperimentROI] = await service.rank_experiments_by_emotional_roi(
        experiment_ids=exp_id_list,
        db=db,
    )

    return ExperimentPrioritizationResponse(
        experiments=[
            {
                "experiment_id": exp.experiment_id,
                "roi_score": exp.roi_score,
                "primary_emotion_opportunity": exp.primary_emotion_opportunity,
                "estimated_lift": exp.estimated_lift,
                "avg_frustration_reduction_potential": exp.avg_frustration_reduction_potential,
                "current_avg_frustration": exp.current_avg_frustration,
            }
            for exp in rankings
        ],
        generated_at=datetime.now(UTC).isoformat(),
    )


# ── ENDPOINTS: Churn Risk ───────────────────────────────────────


@router.get(
    "/session/{session_id}/churn-risk",
    response_model=ChurnRiskResponse,
    summary="Predict churn risk for a session",
)
@limiter.limit("200/minute")
async def predict_churn_risk(
    request: Request,
    session_id: str,
    db: Any = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Predict churn risk for a session using emotion scores."""
    await authenticate_sdk_key(db, sdk_key_hash)

    churn_risk = await service.predict_churn_risk(
        session_id=session_id,
        db=db,
    )

    return ChurnRiskResponse(
        session_id=session_id,
        churn_risk=churn_risk,
        calculated_at=datetime.now(UTC).isoformat(),
    )


# ── ENDPOINTS: Frustration Spike Alerts ─────────────────────────────


@router.get(
    "/experiments/{experiment_id}/frustration-spike",
    response_model=FrustrationSpikeResponse,
    summary="Check for frustration spike",
)
@limiter.limit("100/minute")
async def check_frustration_spike(
    request: Request,
    experiment_id: str,
    window_minutes: int = Query(15, ge=5, le=60, description="Time window in minutes"),
    db: Any = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Check for frustration spike in recent events.

    Returns True if frustration events exceed 2 standard deviations
    above rolling mean in the specified window.
    """
    await authenticate_sdk_key(db, sdk_key_hash)

    spike_detected = await service.check_frustration_spike(
        experiment_id=experiment_id,
        window_minutes=window_minutes,
        db=db,
    )

    return FrustrationSpikeResponse(
        experiment_id=experiment_id,
        spike_detected=spike_detected,
        window_minutes=window_minutes,
        checked_at=datetime.now(UTC).isoformat(),
    )


# ── WEBSOCKET: Real-time Emotion Updates ────────────────────────────


@router.websocket("/ws/{session_id}")
async def emotion_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket endpoint for real-time emotion updates.

    Clients connect to receive live emotion classifications
    as they occur for their session.
    """
    await ws_manager.connect(websocket, session_id)

    try:
        while True:
            # Receive client messages (could be acknowledgments)
            data = await websocket.receive_json()

            # Echo back or process
            if data.get("action") == "ping":
                await websocket.send_json({"action": "pong", "session_id": session_id})

    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        ws_manager.disconnect(session_id)


# ── Helper: Send Emotion Update via WebSocket ───────────────────


async def broadcast_emotion_update(session_id: str, emotion_data: dict) -> None:
    """Send emotion update to connected WebSocket client.

    Can be called from the EmotionService after classification.

    Args:
        session_id: Session identifier.
        emotion_data: Emotion classification data to broadcast.
    """
    message = {
        "session_id": session_id,
        "event": "emotion_update",
        "data": emotion_data,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    await ws_manager.send_emotion_update(session_id, message)
