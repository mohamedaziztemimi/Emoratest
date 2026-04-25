"""Dashboard API endpoints — session retrieval and analytics (CONV-37 to CONV-40).

All endpoints are merchant-scoped: a merchant can only see their own data.
Authentication uses JWT bearer tokens (merchant login), not SDK keys.

Endpoints:
    GET  /api/v1/dashboard/sessions              — paginated session list
    GET  /api/v1/dashboard/sessions/{id}          — full session detail
    GET  /api/v1/dashboard/emotion-trends        — 7-day emotion/friction trends
    GET  /api/v1/dashboard/confusion-pages       — top pages by friction score
    GET  /api/v1/dashboard/analytics/friction-map - element friction heatmap
    GET  /api/v1/dashboard/analytics/funnel       — conversion funnel
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_merchant
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.event import Event, EventEnriched
from app.models.merchant import Merchant
from app.models.session import Session
from app.models.session_features import SessionFeatures
from app.schemas.dashboard import (
    DashboardStatsResponse,
    DropOffReasonItem,
    DropOffReasonsResponse,
    ElementEmotionItem,
    ElementEmotionResponse,
    EmotionConversionItem,
    EmotionConversionResponse,
    EmotionTrendDay,
    EmotionTrendResponse,
    EventOut,
    FrictionMapItem,
    FrictionMapResponse,
    FunnelResponse,
    FunnelStep,
    HeatmapPoint,
    HeatmapResponse,
    HeatmapSession,
    SessionDetailResponse,
    SessionFeaturesOut,
    SessionListItem,
    SessionListResponse,
    WhyAnalysisSummary,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ── GET /emotion-pulse — emotion score metric for overview (Prompt 14) ────


@router.get("/emotion-pulse")
@limiter.limit("100/minute")
async def get_emotion_pulse(
    request: Request,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get emotion score and pulse metrics for overview page.

    Returns weighted emotion score, trend, and session counts.
    Emotion score = (satisfaction + delight) - (frustration + confusion), normalized 0-100.
    """
    from sqlalchemy import Date, cast

    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    # Count sessions with emotions for today
    today_result = await db.execute(
        select(func.count()).where(
            Session.merchant_id == merchant.id,
            Session.started_at >= today_start,
            Session.primary_emotion.isnot(None),
        )
    )
    sessions_today = today_result.scalar() or 0

    # Count sessions with negative emotions today
    negative_result = await db.execute(
        select(func.count()).where(
            Session.merchant_id == merchant.id,
            Session.started_at >= today_start,
            Session.primary_emotion.in_(["frustration", "confusion", "anxiety"]),
        )
    )
    sessions_with_issues = negative_result.scalar() or 0

    # Count active experiments
    exp_result = await db.execute(
        select(func.count()).where(
            Experiment.merchant_id == merchant.id,
            Experiment.is_active == True,
        )
    )
    active_experiments = exp_result.scalar() or 0

    # Count pages with frustration > 30% in last 24h
    pages_result = await db.execute(
        select(func.count(func.distinct(Session.page_url))).where(
            Session.merchant_id == merchant.id,
            Session.started_at >= today_start,
            Session.primary_emotion == "frustration",
        )
    )
    frustration_alerts = pages_result.scalar() or 0

    # Calculate emotion score from all sessions
    # Positive emotions: satisfaction, delight, focus
    # Negative emotions: frustration, confusion, anxiety, hesitation, boredom
    pos_emotions = await db.execute(
        select(func.count()).where(
            Session.merchant_id == merchant.id,
            Session.started_at >= today_start,
            Session.primary_emotion.in_(["satisfaction", "delight", "focus"]),
        )
    )
    pos_count = pos_emotions.scalar() or 0

    neg_emotions = await db.execute(
        select(func.count()).where(
            Session.merchant_id == merchant.id,
            Session.started_at >= today_start,
            Session.primary_emotion.in_(["frustration", "confusion", "anxiety", "hesitation", "boredom"]),
        )
    )
    neg_count = neg_emotions.scalar() or 0

    total_emotional = pos_count + neg_count
    emotion_score = 0
    if total_emotional > 0:
        emotion_score = int((pos_count / total_emotional) * 100)

    # Calculate trend: compare today vs yesterday
    yesterday_start = today_start - timedelta(days=1)
    yesterday_end = today_start

    pos_yesterday = await db.execute(
        select(func.count()).where(
            Session.merchant_id == merchant.id,
            Session.started_at >= yesterday_start,
            Session.started_at < yesterday_end,
            Session.primary_emotion.in_(["satisfaction", "delight", "focus"]),
        )
    )
    pos_yest = pos_yesterday.scalar() or 0

    neg_yesterday = await db.execute(
        select(func.count()).where(
            Session.merchant_id == merchant.id,
            Session.started_at >= yesterday_start,
            Session.started_at < yesterday_end,
            Session.primary_emotion.in_(["frustration", "confusion", "anxiety", "hesitation", "boredom"]),
        )
    )
    neg_yest = neg_yesterday.scalar() or 0

    total_yest = pos_yest + neg_yest
    score_yesterday = 0
    if total_yest > 0:
        score_yesterday = int((pos_yest / total_yest) * 100)

    emotion_trend = emotion_score - score_yesterday

    return {
        "emotion_score": emotion_score,
        "emotion_trend": emotion_trend,
        "sessions_today": sessions_today,
        "sessions_with_issues": sessions_with_issues,
        "frustration_alerts": frustration_alerts,
        "active_experiments": active_experiments,
    }


# ── GET /top-issue — top issue page for overview (Prompt 15) ─────────────


@router.get("/top-issue")
@limiter.limit("100/minute")
async def get_top_issue(
    request: Request,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get the page with highest frustration percentage in last 24h.

    Returns the page with the most critical issue, or {has_issue: false} if none.
    """
    now = datetime.now(UTC)
    day_ago = now - timedelta(hours=24)

    # Get all pages with sessions in last 24h
    pages_result = await db.execute(
        select(
            Session.page_url,
            func.count().label("total"),
            func.sum(case((Session.primary_emotion == "frustration", 1), else_=0)).label("frustration_count"),
            func.sum(case((Event.type == "click", 1), else_=0)).label("click_count"),
        )
        .join(Event, Event.session_id == Session.id)
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= day_ago,
        )
        .group_by(Session.page_url)
        .having(func.count() >= 3)  # Minimum 3 sessions for meaningful data
    )
    pages = pages_result.all()

    if not pages:
        return {"has_issue": False}

    # Find page with highest frustration %
    worst_page = None
    worst_pct = 0

    for page in pages:
        total = page.total or 0
        frustration_pct = (page.frustration_count or 0) / total * 100 if total > 0 else 0

        if frustration_pct > worst_pct and frustration_pct >= 20:  # Minimum 20% threshold
            worst_pct = frustration_pct
            worst_page = page

    if worst_page is None:
        return {"has_issue": False}

    # Determine severity based on rage clicks
    rage_clicks = await db.execute(
        select(func.count()).where(
            Event.session_id.in_(
                select(Session.id).where(
                    Session.merchant_id == merchant.id,
                    Session.page_url == worst_page.page_url,
                    Session.started_at >= day_ago,
                )
            ),
            Event.type == "click",
            Event.metadata_.isnot(None),
        )
    )
    rage_count = rage_clicks.scalar() or 0

    # Determine severity
    severity = "medium" if worst_pct < 30 else "high"
    issue_type = "Rage click spike" if rage_count > 5 else "Frustration spike"

    # Get page title from URL
    from urllib.parse import urlparse
    parsed = urlparse(worst_page.page_url)
    page_title = parsed.path or worst_page.page_url
    if page_title == "/":
        page_title = "Home"
    else:
        page_title = page_title.strip("/").capitalize() or "Page"

    return {
        "has_issue": True,
        "page_url": worst_page.page_url,
        "page_title": page_title,
        "issue_type": issue_type,
        "severity": severity,
        "affected_sessions": worst_page.total,
        "frustration_pct": round(worst_pct),
        "time_window": "24h",
    }


# ── GET /pages-attention — pages needing attention (Prompt 16) ─────────────


@router.get("/pages-attention")
@limiter.limit("100/minute")
async def get_pages_attention(
    request: Request,
    limit: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get top pages with negative emotions in last 7 days.

    Returns pages ranked by dominant negative emotion percentage.
    """
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)

    # Negative emotions: frustration, confusion, anxiety, hesitation
    negative_emotions = ["frustration", "confusion", "anxiety", "hesitation"]

    result = await db.execute(
        select(
            Session.page_url,
            func.count().label("total_sessions"),
            func.sum(case((Session.primary_emotion == "frustration", 1), else_=0)).label("frustration"),
            func.sum(case((Session.primary_emotion == "confusion", 1), else_=0)).label("confusion"),
            func.sum(case((Session.primary_emotion == "anxiety", 1), else_=0)).label("anxiety"),
            func.sum(case((Session.primary_emotion == "hesitation", 1), else_=0)).label("hesitation"),
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= week_ago,
            Session.primary_emotion.isnot(None),
        )
        .group_by(Session.page_url)
        .having(func.count() >= 3)
        .order_by(func.sum(case((Session.primary_emotion.in_(negative_emotions), 1), else_=0)).desc())
        .limit(limit)
    )
    pages = result.all()

    pages_list = []
    for page in pages:
        total = page.total_sessions or 0
        frust = page.frustration or 0
        conf = page.confusion or 0
        anx = page.anxiety or 0
        hes = page.hesitation or 0

        # Find dominant negative emotion
        neg_counts = {
            "frustration": frust,
            "confusion": conf,
            "anxiety": anx,
            "hesitation": hes,
        }
        dominant_emotion = max(neg_counts, key=neg_counts.get)
        emotion_pct = neg_counts[dominant_emotion] / total * 100 if total > 0 else 0

        if emotion_pct >= 15:  # Only include pages with meaningful negative emotion
            pages_list.append({
                "page_url": page.page_url,
                "dominant_emotion": dominant_emotion,
                "emotion_pct": round(emotion_pct),
                "session_count": total,
            })

    return pages_list


# ── GET /problem-sessions — sessions needing attention (Prompt 17) ─────────


@router.get("/problem-sessions")
@limiter.limit("100/minute")
async def get_problem_sessions(
    request: Request,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get recent sessions with negative primary emotions.

    Returns sessions where primary_emotion is frustration, confusion, or anxiety.
    """
    negative_emotions = ["frustration", "confusion", "anxiety"]

    result = await db.execute(
        select(Session)
        .where(
            Session.merchant_id == merchant.id,
            Session.primary_emotion.in_(negative_emotions),
        )
        .order_by(Session.started_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()

    # Get duration from features if available
    session_ids = [s.id for s in sessions]
    features_map = {}
    if session_ids:
        features_result = await db.execute(
            select(SessionFeatures.session_id, SessionFeatures.session_duration_s)
            .where(SessionFeatures.session_id.in_(session_ids))
        )
        for row in features_result:
            features_map[row.session_id] = row.session_duration_s

    sessions_list = []
    for session in sessions:
        # Extract visitor_id from URL or use first 8 chars of session id
        visitor_id = str(session.id)[:8]

        # Get page name
        from urllib.parse import urlparse
        parsed = urlparse(session.page_url)
        page = parsed.path or session.page_url

        duration = features_map.get(session.id)

        sessions_list.append({
            "id": str(session.id),
            "visitor_id": visitor_id,
            "page_url": page,
            "primary_emotion": session.primary_emotion,
            "emotion_confidence": round(session.emotion_confidence * 100) if session.emotion_confidence else None,
            "created_at": session.started_at.isoformat(),
            "duration_seconds": duration,
        })

    return sessions_list


# ── GET /stats — summary stats for dashboard overview ───────────────


@router.get("/stats", response_model=DashboardStatsResponse)
@limiter.limit("100/minute")
async def get_dashboard_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get summary stats for the dashboard overview page."""
    # Calculate average emotion confidence for this merchant
    result = await db.execute(
        select(func.avg(Session.emotion_confidence))
        .where(
            Session.merchant_id == merchant.id,
            Session.emotion_confidence.isnot(None),
        )
    )
    avg_confidence = result.scalar()

    # Count frustration sessions
    frustration_result = await db.execute(
        select(func.count()).where(
            Session.merchant_id == merchant.id,
            Session.primary_emotion == "frustration",
        )
    )
    frustration_count = frustration_result.scalar() or 0

    return DashboardStatsResponse(
        avg_emotion_confidence=round(float(avg_confidence), 4) if avg_confidence is not None else None,
        frustration_count=frustration_count,
    )


# ── GET /sessions — paginated, filtered list (CONV-37) ────────────


@router.get("/sessions", response_model=SessionListResponse)
@limiter.limit("200/minute")
async def list_sessions(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    outcome: str | None = Query(None, pattern=r"^(purchase|abandon|browse|unknown)$"),
    risk_min: float | None = Query(None, ge=0.0, le=1.0),
    risk_max: float | None = Query(None, ge=0.0, le=1.0),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    device_type: str | None = Query(None, pattern=r"^(desktop|mobile|tablet)$"),
    emotion: str | None = Query(None, description="Filter by primary emotion"),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """List sessions for the authenticated merchant with filtering.
    Accepts both full ISO datetime and date-only strings (YYYY-MM-DD).
    """

    query = select(Session).where(Session.merchant_id == merchant.id)

    # Apply filters
    if outcome:
        query = query.where(Session.outcome == outcome)
    if risk_min is not None:
        query = query.where(Session.abandonment_risk >= risk_min)
    if risk_max is not None:
        query = query.where(Session.abandonment_risk <= risk_max)
    if date_from:
        query = query.where(Session.started_at >= date_from)
    if date_to:
        query = query.where(Session.started_at <= date_to)
    if device_type:
        query = query.where(Session.device_type == device_type)
    if emotion:
        query = query.where(Session.primary_emotion == emotion)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Session.started_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    sessions = result.scalars().all()

    return SessionListResponse(
        sessions=[
            SessionListItem(
                id=str(s.id),
                page_url=s.page_url,
                started_at=s.started_at,
                ended_at=s.ended_at,
                outcome=s.outcome,
                abandonment_risk=s.abandonment_risk,
                friction_score=s.friction_score,
                intent_label=s.intent_label,
                country_code=s.country_code,
                device_type=s.device_type,
                primary_emotion=s.primary_emotion,
                emotion_confidence=round(s.emotion_confidence * 100)
                    if s.emotion_confidence else None,
                valence=s.valence,
                arousal=s.arousal,
            )
            for s in sessions
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET /sessions/{id} — full detail (CONV-38) ───────────────────


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
@limiter.limit("200/minute")
async def get_session_detail(
    request: Request,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get full session detail including events, features, and scores."""

    try:
        sid = uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session ID") from exc

    # Load session
    result = await db.execute(
        select(Session).where(Session.id == sid, Session.merchant_id == merchant.id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load events with enriched data if available
    events_result = await db.execute(
        select(Event).where(Event.session_id == sid).order_by(Event.ts)
    )
    events = events_result.scalars().all()

    # Load enriched events for UI-friendly descriptions
    enriched_result = await db.execute(
        select(EventEnriched).where(EventEnriched.session_id == sid).order_by(EventEnriched.ts)
    )
    enriched_events = enriched_result.scalars().all()
    enriched_map = {e.event_id: e.readable_description for e in enriched_events}

    # Load features
    features_result = await db.execute(
        select(SessionFeatures).where(SessionFeatures.session_id == sid)
    )
    features_row = features_result.scalar_one_or_none()

    features_out = None
    if features_row:
        features_out = SessionFeaturesOut(
            hesitation_score=features_row.hesitation_score,
            price_dwell_time_s=features_row.price_dwell_time_s,
            rage_click_score=features_row.rage_click_score,
            scroll_retreat_count=features_row.scroll_retreat_count,
            exit_intent_count=features_row.exit_intent_count,
            checkout_hesitation_s=features_row.checkout_hesitation_s,
            velocity_variance=features_row.velocity_variance,
            session_duration_s=features_row.session_duration_s,
            computed_at=features_row.computed_at,
        )

    return SessionDetailResponse(
        id=str(session.id),
        page_url=session.page_url,
        started_at=session.started_at,
        ended_at=session.ended_at,
        outcome=session.outcome,
        abandonment_risk=session.abandonment_risk,
        friction_score=session.friction_score,
        intent_label=session.intent_label,
        country_code=session.country_code,
        device_type=session.device_type,
        primary_emotion=session.primary_emotion,
        emotion_confidence=session.emotion_confidence,
        emotion_scores=session.emotion_scores,
        valence=session.valence,
        arousal=session.arousal,
        events=[
            EventOut(
                id=e.id,
                type=e.type,
                ts=e.ts,
                x=e.x,
                y=e.y,
                velocity=e.velocity,
                element_id=e.element_id,
                metadata=e.metadata_,
                # Semantic enrichment fields
                label=e.label,
                element_type=e.element_type,
                section=e.section,
                selector=e.selector,
                # Enriched readable description (if available)
                readable_description=enriched_map.get(e.id),
            )
            for e in events
        ],
        features=features_out,
    )


# ── GET /analytics/friction-map (CONV-39) ─────────────────────────


@router.get("/analytics/friction-map", response_model=FrictionMapResponse)
@limiter.limit("200/minute")
async def get_friction_map(
    request: Request,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Aggregate friction data by element_id for heatmap visualization.

    Returns elements ranked by event count, with average hesitation time,
    click count, and rage-click rate.
    """

    # Build base query: events from merchant's sessions with a non-null element_id
    session_ids = (
        select(Session.id)
        .where(Session.merchant_id == merchant.id)
    )
    if date_from:
        session_ids = session_ids.where(Session.started_at >= date_from)
    if date_to:
        session_ids = session_ids.where(Session.started_at <= date_to)

    # Single aggregation query — no N+1 (CONV-44)
    query = (
        select(
            Event.element_id,
            func.count().label("event_count"),
            func.count(
                case((Event.type == "click", 1))
            ).label("click_count"),
            func.count(
                case((
                    (Event.type == "click") & (Event.metadata_.isnot(None)),
                    1,
                ))
            ).label("rage_click_count"),
            func.avg(
                case((Event.velocity.isnot(None), Event.velocity))
            ).label("avg_velocity"),
        )
        .where(
            Event.session_id.in_(session_ids),
            Event.element_id.isnot(None),
        )
        .group_by(Event.element_id)
        .order_by(func.count().desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    elements: list[FrictionMapItem] = []
    for row in rows:
        click_count = row.click_count or 0
        rage_count = row.rage_click_count or 0
        rage_rate = rage_count / click_count if click_count > 0 else 0.0
        avg_velocity = float(row.avg_velocity) if row.avg_velocity is not None else 0.0
        # Invert: low velocity = high hesitation. Normalize to 0-1 scale.
        avg_hesitation = min(1.0, 1.0 / (1.0 + avg_velocity / 100.0))

        elements.append(
            FrictionMapItem(
                element_id=row.element_id,
                event_count=row.event_count,
                avg_hesitation=round(avg_hesitation, 4),
                click_count=click_count,
                rage_click_count=rage_count,
                rage_click_rate=round(rage_rate, 4),
            )
        )

    return FrictionMapResponse(
        elements=elements,
        total_elements=len(elements),
        date_from=date_from,
        date_to=date_to,
    )


# ── GET /analytics/heatmap (Raw x,y coordinates) ─────────────────────


@router.get("/analytics/heatmap", response_model=HeatmapResponse)
@limiter.limit("200/minute")
async def get_heatmap_data(
    request: Request,
    page_url: str | None = Query(None, description="Filter by page URL"),
    event_type: str = Query("click", description="Event type: click, scroll, move"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get raw x,y event coordinates for heatmap visualization."""

    # Get merchant's session IDs
    session_query = select(Session.id).where(Session.merchant_id == merchant.id)
    if page_url:
        session_query = session_query.where(Session.page_url.contains(page_url))
    if date_from:
        session_query = session_query.where(Session.started_at >= date_from)
    if date_to:
        session_query = session_query.where(Session.started_at <= date_to)

    # Map event_type to actual event types in DB
    type_map = {
        "click": ["click"],
        "scroll": ["scroll"],
        "move": ["mouse_move"],
    }
    event_types = type_map.get(event_type, ["click"])

    # Get events with x,y coordinates
    events_query = (
        select(Event.x, Event.y, Event.velocity, Event.type)
        .where(
            Event.session_id.in_(session_query),
            Event.type.in_(event_types),
            Event.x.isnot(None),
            Event.y.isnot(None),
        )
        .order_by(Event.ts.desc())
        .limit(limit)
    )

    result = await db.execute(events_query)
    rows = result.all()

    points = []
    for row in rows:
        value = 1.0
        if row.velocity is not None:
            value = min(1.0, row.velocity / 1000.0)
        points.append(HeatmapPoint(
            x=float(row.x),
            y=float(row.y),
            value=value,
            type=row.type,
        ))

    # Get sessions with emotion data for this page
    sessions_query = (
        select(Session.id, Session.started_at, Session.primary_emotion, Session.emotion_confidence)
        .where(Session.merchant_id == merchant.id)
    )
    if page_url:
        sessions_query = sessions_query.where(Session.page_url.contains(page_url))
    if date_from:
        sessions_query = sessions_query.where(Session.started_at >= date_from)
    if date_to:
        sessions_query = sessions_query.where(Session.started_at <= date_to)
    sessions_query = sessions_query.order_by(Session.started_at.desc()).limit(50)

    session_result = await db.execute(sessions_query)
    session_rows = session_result.all()

    sessions = [
        HeatmapSession(
            id=str(row.id),
            started_at=row.started_at,
            dominant_emotion=row.primary_emotion,
            emotion_confidence=row.emotion_confidence,
        )
        for row in session_rows
    ]

    return HeatmapResponse(
        points=points,
        sessions=sessions,
        total_points=len(points),
        page_url=page_url,
    )


# ── GET /analytics/element-emotions (per-element emotion data) ─────────────


@router.get("/analytics/element-emotions", response_model=ElementEmotionResponse)
@limiter.limit("200/minute")
async def get_element_emotions(
    request: Request,
    page_url: str | None = Query(None, description="Filter by page URL"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get per-element interaction data with emotion breakdown.

    Aggregates by semantic label when available, falling back to element_id.
    Returns human-readable element information (label, type, section).
    """

    # Get merchant's session IDs
    session_query = select(Session.id).where(Session.merchant_id == merchant.id)
    if page_url:
        session_query = session_query.where(Session.page_url.contains(page_url))
    if date_from:
        session_query = session_query.where(Session.started_at >= date_from)
    if date_to:
        session_query = session_query.where(Session.started_at <= date_to)

    # Aggregate events by semantic fields: prefer label, then element_id
    # Use COALESCE to get the first non-null value from label, element_id
    query = (
        select(
            func.coalesce(Event.label, Event.element_id).label("element_key"),
            Event.element_id.label("raw_element_id"),
            func.max(Event.label).label("label"),
            func.max(Event.element_type).label("element_type"),
            func.max(Event.section).label("section"),
            func.count().label("event_count"),
            func.count(case((Event.type == "click", 1))).label("click_count"),
            func.count(case(((Event.type == "click") & (Event.metadata_.isnot(None)), 1))).label("rage_click_count"),
            func.avg(case((Event.velocity.isnot(None), Event.velocity))).label("avg_velocity"),
            func.count(func.distinct(Event.session_id)).label("session_count"),
        )
        .where(
            Event.session_id.in_(session_query),
            Event.element_id.isnot(None),
        )
        .group_by(func.coalesce(Event.label, Event.element_id), Event.element_id)
        .order_by(func.count().desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    # For each element, get emotion data from sessions that interacted with it
    elements = []
    for row in rows:
        click_count = row.click_count or 0
        rage_count = row.rage_click_count or 0
        rage_rate = rage_count / click_count if click_count > 0 else 0.0
        avg_velocity = float(row.avg_velocity) if row.avg_velocity is not None else 0.0
        avg_hesitation = min(1.0, 1.0 / (1.0 + avg_velocity / 100.0))

        # Get emotions from sessions that had events on this element
        emotion_query = (
            select(
                Session.primary_emotion,
                func.count().label("cnt"),
            )
            .where(
                Session.id.in_(
                    select(func.distinct(Event.session_id)).where(
                        Event.element_id == row.raw_element_id,
                        Event.session_id.in_(session_query),
                    )
                ),
                Session.primary_emotion.isnot(None),
            )
            .group_by(Session.primary_emotion)
            .order_by(func.count().desc())
        )
        emotion_result = await db.execute(emotion_query)
        emotion_rows = emotion_result.all()

        emotion_breakdown = {}
        dominant_emotion = None
        emotion_confidence = None
        total_emotion_sessions = 0

        for erow in emotion_rows:
            emotion_breakdown[erow.primary_emotion] = erow.cnt
            total_emotion_sessions += erow.cnt

        if emotion_rows:
            dominant_emotion = emotion_rows[0].primary_emotion
            emotion_confidence = emotion_rows[0].cnt / total_emotion_sessions if total_emotion_sessions > 0 else None

        # Convert counts to percentages
        if total_emotion_sessions > 0:
            emotion_breakdown = {k: round(v / total_emotion_sessions * 100, 1) for k, v in emotion_breakdown.items()}

        elements.append(ElementEmotionItem(
            element_id=row.element_key,  # Use semantic key as display ID
            label=row.label,
            element_type=row.element_type,
            section=row.section,
            event_count=row.event_count,
            click_count=click_count,
            rage_click_count=rage_count,
            rage_click_rate=round(rage_rate, 4),
            avg_hesitation=round(avg_hesitation, 4),
            dominant_emotion=dominant_emotion,
            emotion_confidence=emotion_confidence,
            emotion_breakdown=emotion_breakdown,
            session_count=row.session_count,
        ))

    return ElementEmotionResponse(
        elements=elements,
        total_elements=len(elements),
        page_url=page_url,
    )


# ── GET /analytics/funnel (CONV-40) ──────────────────────────────


@router.get("/analytics/funnel", response_model=FunnelResponse)
@limiter.limit("200/minute")
async def get_funnel(
    request: Request,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Conversion funnel with drop-off rates and friction scores per step.

    Steps are derived from session data:
    1. landing  — all sessions
    2. engaged  — sessions with > 5 events
    3. intent   — sessions with scroll or click events
    4. checkout — sessions with checkout-related element interactions
    5. converted — sessions with outcome='purchase'
    """

    # Base: merchant sessions
    base = select(Session).where(Session.merchant_id == merchant.id)
    if date_from:
        base = base.where(Session.started_at >= date_from)
    if date_to:
        base = base.where(Session.started_at <= date_to)

    # Count total sessions
    total_result = await db.execute(
        select(func.count()).select_from(base.subquery())
    )
    total = total_result.scalar() or 0

    if total == 0:
        return FunnelResponse(
            steps=[], total_sessions=0, conversion_rate=0.0,
            date_from=date_from, date_to=date_to,
        )

    base_ids = select(Session.id).where(Session.merchant_id == merchant.id)
    if date_from:
        base_ids = base_ids.where(Session.started_at >= date_from)
    if date_to:
        base_ids = base_ids.where(Session.started_at <= date_to)

    # Step 2: engaged (sessions with > 5 events)
    engaged_sub = (
        select(Event.session_id)
        .where(Event.session_id.in_(base_ids))
        .group_by(Event.session_id)
        .having(func.count(Event.id) > 5)
    )
    engaged_result = await db.execute(
        select(func.count()).select_from(engaged_sub.subquery())
    )
    engaged = engaged_result.scalar() or 0

    # Step 3: intent (sessions with click or scroll events)
    intent_sub = (
        select(func.distinct(Event.session_id))
        .where(
            Event.session_id.in_(base_ids),
            Event.type.in_(["click", "scroll"]),
        )
    )
    intent_result = await db.execute(
        select(func.count()).select_from(intent_sub.subquery())
    )
    intent = intent_result.scalar() or 0

    # Step 4: checkout (sessions with checkout-related elements)
    checkout_keywords = [
        "%checkout%", "%payment%", "%shipping%",
        "%billing%", "%submit%", "%buy%", "%cart%",
    ]
    checkout_conditions = [Event.element_id.ilike(kw) for kw in checkout_keywords]
    checkout_sub = (
        select(func.distinct(Event.session_id))
        .where(
            Event.session_id.in_(base_ids),
            Event.element_id.isnot(None),
            or_(*checkout_conditions),
        )
    )
    checkout_result = await db.execute(
        select(func.count()).select_from(checkout_sub.subquery())
    )
    checkout = checkout_result.scalar() or 0

    # Step 5: converted
    converted_result = await db.execute(
        select(func.count()).select_from(
            base.where(Session.outcome == "purchase").subquery()
        )
    )
    converted = converted_result.scalar() or 0

    # Avg friction score
    avg_friction_all = await _avg_friction(db, base_ids)

    steps_data = [
        ("landing", total, total),
        ("engaged", engaged, total),
        ("intent", intent, engaged or total),
        ("checkout", checkout, intent or engaged or total),
        ("converted", converted, checkout or intent or total),
    ]

    steps = []
    for i, (step_name, count, prev_count) in enumerate(steps_data):
        drop_off = max(0, prev_count - count) if i > 0 else 0
        drop_off_rate = drop_off / prev_count if prev_count > 0 else 0.0
        steps.append(
            FunnelStep(
                step=step_name,
                sessions=count,
                drop_off=drop_off,
                drop_off_rate=round(drop_off_rate, 4),
                avg_friction_score=avg_friction_all,
            )
        )

    conversion_rate = converted / total if total > 0 else 0.0

    return FunnelResponse(
        steps=steps,
        total_sessions=total,
        conversion_rate=round(conversion_rate, 4),
        date_from=date_from,
        date_to=date_to,
    )


async def _avg_friction(db: AsyncSession, session_ids) -> float | None:
    """Get average friction score for a set of session IDs."""
    result = await db.execute(
        select(func.avg(Session.friction_score))
        .where(
            Session.id.in_(session_ids),
            Session.friction_score.isnot(None),
        )
    )
    val = result.scalar()
    return round(float(val), 4) if val is not None else None


# ── Emotion Trends (CONV-40) ─────────────────────────────────────


@router.get("/emotion-trends")
@limiter.limit("200/minute")
async def get_emotion_trends(
    request: Request,
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get 7-day emotion/friction trends for the chart.

    Returns daily averages for friction_score and abandonment_risk,
    which can be mapped to confusion/frustration/delight in the UI.
    """
    from sqlalchemy import Date, cast

    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)

    result = await db.execute(
        select(
            cast(Session.started_at, Date).label("date"),
            func.avg(Session.friction_score).label("avg_friction"),
            func.avg(Session.abandonment_risk).label("avg_risk"),
            func.count(Session.id).label("count"),
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= start_date,
            Session.friction_score.isnot(None),
        )
        .group_by(cast(Session.started_at, Date))
        .order_by(cast(Session.started_at, Date))
    )
    rows = result.all()

    # Build date map
    trend_data = {}
    for row in rows:
        trend_data[str(row.date)] = {
            "friction": round((row.avg_friction or 0) * 100, 1),
            "risk": round((row.avg_risk or 0) * 100, 1),
            "count": row.count,
        }

    # Generate last N days with 0 for missing days
    days_list = []
    for i in range(days - 1, -1, -1):
        day = (end_date - timedelta(days=i)).date()
        day_str = str(day)
        days_list.append(
            {
                "date": day_str,
                "label": day.strftime("%a"),
                "friction": trend_data.get(day_str, {}).get("friction", 0),
                "risk": trend_data.get(day_str, {}).get("risk", 0),
                "count": trend_data.get(day_str, {}).get("count", 0),
            }
        )

    return days_list


@router.get("/confusion-pages")
@limiter.limit("200/minute")
async def get_confusion_pages(
    request: Request,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get top pages by confusion (friction score) for the confused pages list.

    Returns pages with highest average friction scores, limited to pages
    with meaningful friction data.
    """
    result = await db.execute(
        select(
            Session.page_url,
            func.avg(Session.friction_score).label("avg_friction"),
            func.count(Session.id).label("session_count"),
            func.avg(Session.abandonment_risk).label("avg_risk"),
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.friction_score.isnot(None),
            Session.friction_score > 0.1,  # Only pages with meaningful friction
        )
        .group_by(Session.page_url)
        .order_by(func.avg(Session.friction_score).desc())
        .limit(5)
    )
    rows = result.all()

    return [
        {
            "page_url": row.page_url,
            "confusion_score": round((row.avg_friction or 0) * 100),
            "session_count": row.session_count,
            "drop_off_rate": round((row.avg_risk or 0) * 100),
        }
        for row in rows
    ]


# ── Experiments (JWT-authenticated for dashboard) ──────────────


from app.core.security import sanitize_text
from app.models.experiment import Experiment


@router.get("/experiments", response_model=dict)
@limiter.limit("100/minute")
async def list_dashboard_experiments(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """List experiments for the authenticated merchant (JWT auth)."""

    query = select(Experiment).where(Experiment.merchant_id == merchant.id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Experiment.created_at.desc()).offset(offset).limit(page_size)
    rows = await db.execute(query)
    experiments = rows.scalars().all()

    def _experiment_to_out(exp: Experiment) -> dict:
        return {
            "id": str(exp.id),
            "merchant_id": str(exp.merchant_id),
            "title": exp.title,
            "hypothesis": exp.hypothesis,
            "page_element": exp.page_element,
            "friction_type": exp.friction_type,
            "variant_a": exp.variant_a,
            "variant_b": exp.variant_b,
            "result": exp.result,
            "conversion_delta": exp.conversion_delta,
            "sample_size": exp.sample_size,
            "ran_at": exp.ran_at,
            "source": exp.source,
            "created_at": exp.created_at,
            "experiment_type": getattr(exp, "experiment_type", None),
            "n_variants": getattr(exp, "n_variants", None),
            "flicker_free": getattr(exp, "flicker_free", None),
            "is_active": getattr(exp, "is_active", None),
        }

    return {
        "experiments": [_experiment_to_out(e) for e in experiments],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/experiments", response_model=dict, status_code=201)
@limiter.limit("50/minute")
async def create_dashboard_experiment(
    request: Request,
    body: dict,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Create a new experiment (JWT auth)."""
    exp = Experiment(
        merchant_id=merchant.id,
        title=sanitize_text(body.get("title", ""), max_length=256),
        hypothesis=sanitize_text(body.get("hypothesis", ""), max_length=2000) if body.get("hypothesis") else None,
        friction_type=body.get("friction_type"),
        variant_a=sanitize_text(body.get("variant_a", ""), max_length=2000) if body.get("variant_a") else None,
        variant_b=sanitize_text(body.get("variant_b", ""), max_length=2000) if body.get("variant_b") else None,
        source="dashboard",
    )

    db.add(exp)
    await db.commit()
    await db.refresh(exp)

    return {
        "id": str(exp.id),
        "merchant_id": str(exp.merchant_id),
        "title": exp.title,
        "hypothesis": exp.hypothesis,
        "page_element": exp.page_element,
        "friction_type": exp.friction_type,
        "variant_a": exp.variant_a,
        "variant_b": exp.variant_b,
        "result": exp.result,
        "conversion_delta": exp.conversion_delta,
        "sample_size": exp.sample_size,
        "ran_at": exp.ran_at,
        "source": exp.source,
        "created_at": exp.created_at,
    }


@router.delete("/experiments/{experiment_id}", status_code=204)
@limiter.limit("50/minute")
async def delete_dashboard_experiment(
    request: Request,
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Delete an experiment (JWT auth)."""
    import uuid

    try:
        eid = uuid.UUID(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid experiment ID") from exc

    result = await db.execute(
        delete(Experiment)
        .where(Experiment.id == eid, Experiment.merchant_id == merchant.id)
        .returning(Experiment.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    await db.commit()


@router.get("/experiments/{experiment_id}/stats")
@limiter.limit("100/minute")
async def get_dashboard_experiment_stats(
    request: Request,
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get experiment statistics (JWT auth)."""
    import uuid

    from app.services.experiment_service import compute_ab_significance

    try:
        eid = uuid.UUID(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid experiment ID") from exc

    result = await db.execute(
        select(Experiment).where(Experiment.id == eid, Experiment.merchant_id == merchant.id)
    )
    exp = result.scalar_one_or_none()
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if exp.conversion_delta is None or exp.sample_size is None:
        return {
            "experiment_id": str(exp.id),
            "title": exp.title,
            "result": exp.result,
            "conversion_delta": exp.conversion_delta,
            "sample_size": exp.sample_size,
            "confidence_level": None,
            "is_significant": False,
            "p_value": None,
            "power": None,
            "recommendation": "insufficient_data",
        }

    stats = compute_ab_significance(
        conversion_delta=exp.conversion_delta,
        sample_size=exp.sample_size,
    )

    return {
        "experiment_id": str(exp.id),
        "title": exp.title,
        "result": exp.result,
        "conversion_delta": exp.conversion_delta,
        "sample_size": exp.sample_size,
        "confidence_level": stats["confidence_level"],
        "is_significant": stats["is_significant"],
        "p_value": stats["p_value"],
        "power": stats["power"],
        "recommendation": stats["recommendation"],
    }


# ── GET /analytics/why-analysis/emotion-conversion ─────────────────────


@router.get("/analytics/why-analysis/emotion-conversion", response_model=EmotionConversionResponse)
@limiter.limit("200/minute")
async def get_emotion_conversion(
    request: Request,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get conversion breakdown by emotion.

    For each emotion, shows total sessions, converted vs abandoned counts,
    conversion rate, and average friction/risk scores.
    """
    # Base query: sessions with primary_emotion for this merchant
    base_query = select(Session).where(
        Session.merchant_id == merchant.id,
        Session.primary_emotion.isnot(None),
    )
    if date_from:
        base_query = base_query.where(Session.started_at >= date_from)
    if date_to:
        base_query = base_query.where(Session.started_at <= date_to)

    # Count total sessions with emotion
    total_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total_sessions = total_result.scalar() or 0

    if total_sessions == 0:
        return EmotionConversionResponse(
            items=[],
            total_sessions=0,
            overall_conversion_rate=0.0,
        )

    # Group by emotion and aggregate metrics
    query = (
        select(
            Session.primary_emotion,
            func.count().label("total_sessions"),
            func.count(case((Session.outcome == "purchase", 1))).label("converted"),
            func.count(case((Session.outcome != "purchase", 1))).label("abandoned"),
            func.avg(Session.friction_score).label("avg_friction"),
            func.avg(Session.abandonment_risk).label("avg_risk"),
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.primary_emotion.isnot(None),
        )
        .group_by(Session.primary_emotion)
        .order_by(func.count().desc())
    )

    if date_from:
        query = query.where(Session.started_at >= date_from)
    if date_to:
        query = query.where(Session.started_at <= date_to)

    result = await db.execute(query)
    rows = result.all()

    # Calculate overall conversion rate
    total_converted = sum(row.converted for row in rows)
    overall_conversion_rate = total_converted / total_sessions if total_sessions > 0 else 0.0

    items = []
    for row in rows:
        total = row.total_sessions or 0
        converted = row.converted or 0
        abandoned = row.abandoned or 0
        conversion_rate = converted / total if total > 0 else 0.0

        items.append(EmotionConversionItem(
            emotion=row.primary_emotion,
            total_sessions=total,
            converted=converted,
            abandoned=abandoned,
            conversion_rate=round(conversion_rate, 4),
            avg_friction=round(float(row.avg_friction), 4) if row.avg_friction is not None else None,
            avg_abandonment_risk=round(float(row.avg_risk), 4) if row.avg_risk is not None else None,
        ))

    return EmotionConversionResponse(
        items=items,
        total_sessions=total_sessions,
        overall_conversion_rate=round(overall_conversion_rate, 4),
    )


# ── GET /analytics/why-analysis/drop-off-reasons ──────────────────────


@router.get("/analytics/why-analysis/drop-off-reasons", response_model=DropOffReasonsResponse)
@limiter.limit("200/minute")
async def get_drop_off_reasons(
    request: Request,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get top page + emotion combinations causing drop-off.

    Only includes abandoned sessions (outcome != 'purchase').
    Groups by page_url and primary_emotion to identify friction patterns.
    """
    # Count total abandoned sessions with emotion
    base_abandoned = select(Session).where(
        Session.merchant_id == merchant.id,
        Session.primary_emotion.isnot(None),
        Session.outcome != "purchase",
    )
    if date_from:
        base_abandoned = base_abandoned.where(Session.started_at >= date_from)
    if date_to:
        base_abandoned = base_abandoned.where(Session.started_at <= date_to)

    total_abandoned_result = await db.execute(
        select(func.count()).select_from(base_abandoned.subquery())
    )
    total_abandoned = total_abandoned_result.scalar() or 0

    if total_abandoned == 0:
        return DropOffReasonsResponse(
            reasons=[],
            total_patterns=0,
        )

    # Group by page_url and emotion, filter to groups with >= 2 sessions
    query = (
        select(
            Session.page_url,
            Session.primary_emotion,
            func.count().label("sessions"),
            func.avg(Session.friction_score).label("avg_friction"),
            func.avg(Session.abandonment_risk).label("avg_risk"),
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.primary_emotion.isnot(None),
            Session.outcome != "purchase",
        )
        .group_by(Session.page_url, Session.primary_emotion)
        .having(func.count() >= 2)
        .order_by(func.count().desc())
        .limit(limit)
    )

    if date_from:
        query = query.where(Session.started_at >= date_from)
    if date_to:
        query = query.where(Session.started_at <= date_to)

    result = await db.execute(query)
    rows = result.all()

    reasons = []
    for row in rows:
        sessions = row.sessions or 0
        drop_off_rate = sessions / total_abandoned if total_abandoned > 0 else 0.0

        reasons.append(DropOffReasonItem(
            page_url=row.page_url,
            emotion=row.primary_emotion,
            sessions=sessions,
            drop_off_rate=round(drop_off_rate, 4),
            avg_friction=round(float(row.avg_friction), 4) if row.avg_friction is not None else None,
            avg_abandonment_risk=round(float(row.avg_risk), 4) if row.avg_risk is not None else None,
        ))

    return DropOffReasonsResponse(
        reasons=reasons,
        total_patterns=len(reasons),
    )


# ── GET /analytics/why-analysis/summary ────────────────────────────────


@router.get("/analytics/why-analysis/summary", response_model=WhyAnalysisSummary)
@limiter.limit("200/minute")
async def get_why_analysis_summary(
    request: Request,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get summary stats for Why-Analysis dashboard.

    Returns headline numbers including top/bottom performing emotions
    and friction differences between converted and abandoned sessions.
    """
    # Base query for all merchant sessions
    base = select(Session).where(Session.merchant_id == merchant.id)
    if date_from:
        base = base.where(Session.started_at >= date_from)
    if date_to:
        base = base.where(Session.started_at <= date_to)

    # Total sessions
    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total_sessions = total_result.scalar() or 0

    # Sessions with emotion
    with_emotion = base.where(Session.primary_emotion.isnot(None))
    emotion_result = await db.execute(select(func.count()).select_from(with_emotion.subquery()))
    sessions_with_emotion = emotion_result.scalar() or 0

    # Overall conversion rate
    converted_result = await db.execute(
        select(func.count()).select_from(
            base.where(Session.outcome == "purchase").subquery()
        )
    )
    converted = converted_result.scalar() or 0
    overall_conversion_rate = converted / total_sessions if total_sessions > 0 else 0.0

    # Per-emotion conversion rates (for finding top/bottom)
    emotion_query = (
        select(
            Session.primary_emotion,
            func.count().label("total"),
            func.count(case((Session.outcome == "purchase", 1))).label("converted"),
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.primary_emotion.isnot(None),
        )
        .group_by(Session.primary_emotion)
    )

    if date_from:
        emotion_query = emotion_query.where(Session.started_at >= date_from)
    if date_to:
        emotion_query = emotion_query.where(Session.started_at <= date_to)

    emotion_result = await db.execute(emotion_query)
    emotion_rows = emotion_result.all()

    # Find top drop-off emotion (lowest conversion rate, min 1 session)
    # and top converting emotion (highest conversion rate, min 1 session)
    # Ensure they are never the same emotion
    top_drop_off_emotion = None
    top_drop_off_emotion_rate = None
    top_converting_emotion = None
    top_converting_emotion_rate = None

    qualifying_emotions = [(e, e.total, e.converted) for e in emotion_rows if e.total >= 1]
    if qualifying_emotions:
        # Calculate conversion rates for each emotion
        emotions_with_rates = []
        for e, total, converted in qualifying_emotions:
            rate = (converted / total) if total > 0 else 0
            emotions_with_rates.append((e.primary_emotion, rate, total, converted))

        # Sort by conversion rate
        emotions_with_rates.sort(key=lambda x: x[1])

        # Determine best and worst emotions, ensuring they're different
        if len(emotions_with_rates) == 1:
            # Only one emotion: assign it to best converting, leave worst as null
            top_converting_emotion = emotions_with_rates[0][0]
            top_converting_emotion_rate = round(emotions_with_rates[0][1], 4)
        else:
            # Multiple emotions: assign worst (first) and best (last)
            # They're guaranteed to be different since we have at least 2
            worst = emotions_with_rates[0]
            best = emotions_with_rates[-1]

            top_drop_off_emotion = worst[0]
            top_drop_off_emotion_rate = round(worst[1], 4)

            top_converting_emotion = best[0]
            top_converting_emotion_rate = round(best[1], 4)

    # Avg friction for abandoned vs converted
    abandoned_query = select(func.avg(Session.friction_score)).where(
        Session.merchant_id == merchant.id,
        Session.outcome != "purchase",
        Session.friction_score.isnot(None),
    )
    if date_from:
        abandoned_query = abandoned_query.where(Session.started_at >= date_from)
    if date_to:
        abandoned_query = abandoned_query.where(Session.started_at <= date_to)
    abandoned_friction_result = await db.execute(abandoned_query)

    avg_friction_abandoned = abandoned_friction_result.scalar()
    if avg_friction_abandoned is not None:
        avg_friction_abandoned = round(float(avg_friction_abandoned), 4)

    # Avg friction for converted
    converted_query = select(func.avg(Session.friction_score)).where(
        Session.merchant_id == merchant.id,
        Session.outcome == "purchase",
        Session.friction_score.isnot(None),
    )
    if date_from:
        converted_query = converted_query.where(Session.started_at >= date_from)
    if date_to:
        converted_query = converted_query.where(Session.started_at <= date_to)
    converted_friction_result = await db.execute(converted_query)

    avg_friction_converted = converted_friction_result.scalar()
    if avg_friction_converted is not None:
        avg_friction_converted = round(float(avg_friction_converted), 4)

    return WhyAnalysisSummary(
        total_sessions=total_sessions,
        sessions_with_emotion=sessions_with_emotion,
        overall_conversion_rate=round(overall_conversion_rate, 4),
        top_drop_off_emotion=top_drop_off_emotion,
        top_drop_off_emotion_rate=top_drop_off_emotion_rate,
        top_converting_emotion=top_converting_emotion,
        top_converting_emotion_rate=top_converting_emotion_rate,
        avg_friction_abandoned=avg_friction_abandoned,
        avg_friction_converted=avg_friction_converted,
    )


# ── GET /analytics/why-analysis/emotion-trend ─────────────────────────


@router.get("/analytics/why-analysis/emotion-trend", response_model=EmotionTrendResponse)
@limiter.limit("200/minute")
async def get_emotion_trend(
    request: Request,
    days: int = Query(30, ge=1, le=90),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Daily emotion breakdown over time for trend visualization."""
    from sqlalchemy import Date, cast

    # Determine date range
    if date_to:
        end_date = date_to
    else:
        end_date = datetime.now(UTC)

    if date_from:
        start_date = date_from
    else:
        start_date = end_date - timedelta(days=days)

    # Query: group by date and primary_emotion
    result = await db.execute(
        select(
            cast(Session.started_at, Date).label("date"),
            Session.primary_emotion,
            func.count(Session.id).label("cnt"),
            func.count(case((Session.outcome == "purchase", 1))).label("converted"),
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= start_date,
            Session.started_at <= end_date,
            Session.primary_emotion.isnot(None),
        )
        .group_by(cast(Session.started_at, Date), Session.primary_emotion)
        .order_by(cast(Session.started_at, Date))
    )
    rows = result.all()

    # Build day map
    day_map: dict[str, dict] = {}
    all_emotions: set[str] = set()

    for row in rows:
        day_str = str(row.date)
        if day_str not in day_map:
            day_map[day_str] = {"emotions": {}, "total": 0, "converted": 0}
        day_map[day_str]["emotions"][row.primary_emotion] = row.cnt
        day_map[day_str]["total"] += row.cnt
        day_map[day_str]["converted"] += row.converted
        all_emotions.add(row.primary_emotion)

    # Fill in all days in range
    trend_days = []
    current = start_date.date() if hasattr(start_date, "date") else start_date
    end = end_date.date() if hasattr(end_date, "date") else end_date

    while current <= end:
        day_str = str(current)
        info = day_map.get(day_str, {"emotions": {}, "total": 0, "converted": 0})
        conv_rate = info["converted"] / info["total"] if info["total"] > 0 else None
        trend_days.append(EmotionTrendDay(
            date=day_str,
            emotions=info["emotions"],
            total=info["total"],
            conversion_rate=round(conv_rate, 4) if conv_rate is not None else None,
        ))
        current += timedelta(days=1)

    return EmotionTrendResponse(
        days=trend_days,
        emotions_seen=sorted(all_emotions),
    )
