"""Intervention Recommendation & Tracking API (CONV-39).

Provides:
    GET  /interventions/recommend/{session_id}  — get recommendations for a session
    POST /interventions/record                  — record intervention outcome
    GET  /interventions/stats                   — aggregated intervention performance

All endpoints are merchant-scoped via SDK key authentication.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_merchant_flexible
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.intervention_result import InterventionResult
from app.models.merchant import Merchant
from app.models.session import Session
from app.models.session_features import SessionFeatures
from app.schemas.interventions import (
    InterventionRecommendation,
    InterventionResultOut,
    InterventionResultRecordRequest,
    InterventionStatsResponse,
    SessionInterventionsResponse,
)
from app.services.intervention_service import recommend_interventions

router = APIRouter(prefix="/interventions", tags=["interventions"])


# ── RECOMMEND ─────────────────────────────────────────────────────


@router.get("/recommend/{session_id}", response_model=SessionInterventionsResponse)
@limiter.limit("300/minute")
async def get_recommendations(
    request: Request,
    session_id: str,
    max_results: int = Query(3, ge=1, le=8),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Get intervention recommendations for a specific session.

    Uses the session's ML scores and features to rank interventions
    by relevance and estimated conversion lift.
    """

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

    # Load features for fine-grained targeting
    features_result = await db.execute(
        select(SessionFeatures).where(SessionFeatures.session_id == sid)
    )
    features_row = features_result.scalar_one_or_none()
    features_dict = None
    if features_row:
        features_dict = {
            "hesitation_score": features_row.hesitation_score,
            "price_dwell_time_s": features_row.price_dwell_time_s,
            "rage_click_score": features_row.rage_click_score,
            "scroll_retreat_count": features_row.scroll_retreat_count,
            "exit_intent_count": features_row.exit_intent_count,
            "checkout_hesitation_s": features_row.checkout_hesitation_s,
            "velocity_variance": features_row.velocity_variance,
            "session_duration_s": features_row.session_duration_s,
        }

    # Get ranked recommendations
    recs = recommend_interventions(
        abandonment_risk=session.abandonment_risk,
        friction_score=session.friction_score,
        intent_label=session.intent_label,
        features=features_dict,
        page_url=session.page_url,
        primary_emotion=session.primary_emotion,
        max_results=max_results,
    )

    return SessionInterventionsResponse(
        session_id=str(session.id),
        abandonment_risk=session.abandonment_risk,
        friction_score=session.friction_score,
        intent_label=session.intent_label,
        recommendations=[InterventionRecommendation(**r) for r in recs],
        generated_at=datetime.now(UTC),
    )


# ── RECORD OUTCOME ────────────────────────────────────────────────


@router.post("/record", response_model=InterventionResultOut, status_code=201)
@limiter.limit("300/minute")
async def record_intervention_result(
    request: Request,
    body: InterventionResultRecordRequest,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Record the outcome of a triggered intervention."""

    # Validate session_id belongs to merchant
    try:
        sid = uuid.UUID(body.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session ID") from exc

    sess_result = await db.execute(
        select(Session.id).where(Session.id == sid, Session.merchant_id == merchant.id)
    )
    if sess_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate experiment_id if provided
    exp_id = None
    if body.experiment_id:
        try:
            exp_id = uuid.UUID(body.experiment_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid experiment ID") from exc

    record = InterventionResult(
        merchant_id=merchant.id,
        experiment_id=exp_id,
        intervention_id=body.intervention_id,
        triggered_at=datetime.now(UTC),
        session_id=sid,
        outcome=body.outcome,
        conversion_delta=body.conversion_delta,
    )

    db.add(record)
    await db.commit()
    await db.refresh(record)

    return InterventionResultOut(
        id=str(record.id),
        merchant_id=str(record.merchant_id),
        intervention_id=record.intervention_id,
        session_id=str(record.session_id) if record.session_id else None,
        experiment_id=str(record.experiment_id) if record.experiment_id else None,
        triggered_at=record.triggered_at,
        outcome=record.outcome,
        conversion_delta=record.conversion_delta,
    )


# ── AGGREGATED STATS ──────────────────────────────────────────────


@router.get("/stats", response_model=list[InterventionStatsResponse])
@limiter.limit("300/minute")
async def get_intervention_stats(
    request: Request,
    intervention_id: str | None = Query(None, max_length=16),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Get aggregated performance statistics per intervention type.

    Optionally filter to a single intervention_id.
    """

    query = (
        select(
            InterventionResult.intervention_id,
            func.count().label("total_triggers"),
            func.count(
                func.nullif(InterventionResult.outcome != "converted", True)
            ).label("converted"),
            func.count(
                func.nullif(InterventionResult.outcome != "dismissed", True)
            ).label("dismissed"),
            func.count(
                func.nullif(InterventionResult.outcome != "ignored", True)
            ).label("ignored"),
            func.count(
                func.nullif(InterventionResult.outcome != "bounced", True)
            ).label("bounced"),
            func.avg(InterventionResult.conversion_delta).label("avg_delta"),
        )
        .where(InterventionResult.merchant_id == merchant.id)
        .group_by(InterventionResult.intervention_id)
    )

    if intervention_id:
        query = query.where(InterventionResult.intervention_id == intervention_id)

    result = await db.execute(query)
    rows = result.all()

    stats = []
    for row in rows:
        total = row.total_triggers or 0
        converted = row.converted or 0
        conversion_rate = converted / total if total > 0 else 0.0
        stats.append(
            InterventionStatsResponse(
                intervention_id=row.intervention_id,
                total_triggers=total,
                converted=converted,
                dismissed=row.dismissed or 0,
                ignored=row.ignored or 0,
                bounced=row.bounced or 0,
                conversion_rate=round(conversion_rate, 4),
                avg_conversion_delta=(
                    round(float(row.avg_delta), 4) if row.avg_delta is not None else None
                ),
            )
        )

    return stats
