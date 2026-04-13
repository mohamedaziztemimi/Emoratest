"""Dashboard API endpoints — session retrieval and analytics (CONV-37 to CONV-40).

All endpoints are merchant-scoped: a merchant can only see their own data.
Authentication uses JWT bearer tokens (merchant login), not SDK keys.

Endpoints:
    GET  /api/v1/dashboard/sessions              — paginated session list
    GET  /api/v1/dashboard/sessions/{id}          — full session detail
    GET  /api/v1/dashboard/analytics/friction-map — element friction heatmap
    GET  /api/v1/dashboard/analytics/funnel       — conversion funnel
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_merchant
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.event import Event
from app.models.merchant import Merchant
from app.models.session import Session
from app.models.session_features import SessionFeatures
from app.schemas.dashboard import (
    EventOut,
    FrictionMapItem,
    FrictionMapResponse,
    FunnelResponse,
    FunnelStep,
    SessionDetailResponse,
    SessionFeaturesOut,
    SessionListItem,
    SessionListResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ── GET /sessions — paginated, filtered list (CONV-37) ────────────


@router.get("/sessions", response_model=SessionListResponse)
@limiter.limit("200/minute")
async def list_sessions(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    outcome: str | None = Query(None, pattern=r"^(purchase|abandon|unknown)$"),
    risk_min: float | None = Query(None, ge=0.0, le=1.0),
    risk_max: float | None = Query(None, ge=0.0, le=1.0),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    device_type: str | None = Query(None, pattern=r"^(desktop|mobile|tablet)$"),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """List sessions for the authenticated merchant with filtering."""

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

    # Load events
    events_result = await db.execute(
        select(Event).where(Event.session_id == sid).order_by(Event.ts)
    )
    events = events_result.scalars().all()

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
