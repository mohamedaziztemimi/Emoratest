"""Cohort & Segment Analytics API (CONV-40).

Provides:
    GET /analytics/cohorts         — session cohort analysis by dimension
    GET /analytics/risk-distribution — abandonment risk histogram

All endpoints are merchant-scoped via SDK key authentication.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.session import Session
from app.schemas.analytics import (
    CohortAnalyticsResponse,
    CohortBucket,
    RiskDistributionBucket,
    RiskDistributionResponse,
)
from app.services.sdk_auth import authenticate_sdk_key, get_sdk_key_header

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ── COHORT ANALYSIS ───────────────────────────────────────────────


@router.get("/cohorts", response_model=CohortAnalyticsResponse)
@limiter.limit("200/minute")
async def get_cohort_analytics(
    request: Request,
    dimension: str = Query(
        ..., pattern=r"^(device_type|country_code|outcome|intent_label)$",
        description="Dimension to segment sessions by",
    ),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Segment sessions by a dimension and compute conversion metrics per cohort.

    Supported dimensions:
    - device_type: desktop / mobile / tablet
    - country_code: 2-letter ISO codes
    - outcome: purchase / abandon / unknown
    - intent_label: browsing / comparing / buying / returning
    """
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    # Map dimension to column
    dim_column_map = {
        "device_type": Session.device_type,
        "country_code": Session.country_code,
        "outcome": Session.outcome,
        "intent_label": Session.intent_label,
    }
    dim_col = dim_column_map[dimension]

    # Base filter
    base_filter = [Session.merchant_id == merchant.id]
    if date_from:
        base_filter.append(Session.started_at >= date_from)
    if date_to:
        base_filter.append(Session.started_at <= date_to)

    # Aggregate by dimension
    query = (
        select(
            func.coalesce(dim_col, "unknown").label("label"),
            func.count().label("session_count"),
            func.count(
                case((Session.outcome == "purchase", 1))
            ).label("purchase_count"),
            func.count(
                case((Session.outcome == "abandon", 1))
            ).label("abandon_count"),
            func.avg(Session.abandonment_risk).label("avg_risk"),
            func.avg(Session.friction_score).label("avg_friction"),
        )
        .where(*base_filter)
        .group_by(func.coalesce(dim_col, "unknown"))
        .order_by(func.count().desc())
    )

    result = await db.execute(query)
    rows = result.all()

    # Total sessions for overall rate
    total_sessions = sum(r.session_count for r in rows)
    total_purchases = sum(r.purchase_count for r in rows)

    buckets = []
    for row in rows:
        count = row.session_count
        purchases = row.purchase_count
        conv_rate = purchases / count if count > 0 else 0.0
        buckets.append(
            CohortBucket(
                label=str(row.label),
                session_count=count,
                purchase_count=purchases,
                abandon_count=row.abandon_count,
                conversion_rate=round(conv_rate, 4),
                avg_abandonment_risk=(
                    round(float(row.avg_risk), 4) if row.avg_risk is not None else None
                ),
                avg_friction_score=(
                    round(float(row.avg_friction), 4) if row.avg_friction is not None else None
                ),
            )
        )

    overall_rate = total_purchases / total_sessions if total_sessions > 0 else 0.0

    return CohortAnalyticsResponse(
        dimension=dimension,
        buckets=buckets,
        total_sessions=total_sessions,
        overall_conversion_rate=round(overall_rate, 4),
        date_from=date_from,
        date_to=date_to,
    )


# ── RISK DISTRIBUTION ────────────────────────────────────────────


@router.get("/risk-distribution", response_model=RiskDistributionResponse)
@limiter.limit("200/minute")
async def get_risk_distribution(
    request: Request,
    buckets_count: int = Query(10, ge=2, le=20, alias="buckets"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Get the distribution of abandonment risk scores across sessions.

    Returns a histogram with configurable bucket count (default 10).
    Only includes sessions that have been scored (abandonment_risk IS NOT NULL).
    """
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    base_filter = [
        Session.merchant_id == merchant.id,
        Session.abandonment_risk.isnot(None),
    ]
    if date_from:
        base_filter.append(Session.started_at >= date_from)
    if date_to:
        base_filter.append(Session.started_at <= date_to)

    # Get all risk scores for bucketing
    query = select(Session.abandonment_risk, Session.outcome).where(*base_filter)
    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return RiskDistributionResponse(
            buckets=[], total_sessions=0, avg_risk=None, median_risk=None,
        )

    # Build histogram buckets
    bucket_width = 1.0 / buckets_count
    histogram: dict[int, list] = {i: [] for i in range(buckets_count)}

    for row in rows:
        risk = row.abandonment_risk
        bucket_idx = min(int(risk / bucket_width), buckets_count - 1)
        histogram[bucket_idx].append(row.outcome)

    buckets = []
    for i in range(buckets_count):
        range_min = round(i * bucket_width, 2)
        range_max = round((i + 1) * bucket_width, 2)
        outcomes = histogram[i]
        count = len(outcomes)
        purchases = sum(1 for o in outcomes if o == "purchase")
        conv_rate = purchases / count if count > 0 else 0.0

        buckets.append(
            RiskDistributionBucket(
                range_label=f"{range_min:.1f}-{range_max:.1f}",
                range_min=range_min,
                range_max=range_max,
                session_count=count,
                conversion_rate=round(conv_rate, 4),
            )
        )

    # Summary stats
    risks = sorted([r.abandonment_risk for r in rows])
    total = len(risks)
    avg_risk = sum(risks) / total
    median_risk = risks[total // 2]

    return RiskDistributionResponse(
        buckets=buckets,
        total_sessions=total,
        avg_risk=round(avg_risk, 4),
        median_risk=round(median_risk, 4),
    )
