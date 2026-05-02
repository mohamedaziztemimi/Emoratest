"""Pages API — page-level emotion analysis insights."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.auth import get_merchant_id as get_merchant_flexible
from app.core.auth import get_current_merchant
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.event import Event
from app.models.merchant import Merchant
from app.models.session import Session

router = APIRouter(prefix="/api/v1/pages", tags=["pages"])


# ── Schemas ─────────────────────────────────────────────────────────


class PageInsightItem(BaseModel):
    page_url: str
    session_count: int
    dominant_emotion: str
    dominant_emotion_pct: float
    rage_clicks: int
    avg_duration_seconds: float
    top_signals: list[str]

    class Config:
        from_attributes = True


class PageInsightsResponse(BaseModel):
    pages: list[PageInsightItem]
    total_pages: int


class PageDetailInsight(BaseModel):
    page_url: str
    total_sessions: int
    emotion_breakdown: dict[str, float]
    trend: dict[str, float]
    interactive_elements: list[dict]
    recent_sessions: list[dict]


# ── Helpers ─────────────────────────────────────────────────────────


NEGATIVE_EMOTIONS = ["frustration", "confusion", "anxiety", "hesitation"]


def _get_dominant_emotion(emotions: dict) -> tuple[str, float]:
    """Get the dominant emotion and its percentage from emotion scores."""
    if not emotions:
        return "unknown", 0.0

    max_emotion = max(emotions.items(), key=lambda x: x[1])
    return max_emotion[0], round(max_emotion[1] * 100, 1)


def _get_dominant_negative(emotions: dict) -> tuple[str, float]:
    """Get the dominant negative emotion and its percentage."""
    if not emotions:
        return "none", 0.0

    negative = {k: v for k, v in emotions.items() if k in NEGATIVE_EMOTIONS}
    if not negative:
        return "none", 0.0

    max_emotion = max(negative.items(), key=lambda x: x[1])
    return max_emotion[0], round(max_emotion[1] * 100, 1)


# ── Endpoints ───────────────────────────────────────────────────────
# IMPORTANT: Route order matters for FastAPI! More specific routes must be
# defined BEFORE parameterized routes. Otherwise, "/insights/detail" would
# match "/insights/{encoded_page}" with encoded_page="detail".
# Always keep: /insights → /insights/detail → /insights/{encoded_page}


@router.get("/insights", response_model=PageInsightsResponse, summary="Get page insights")
@limiter.limit("60/minute")
async def get_page_insights(
    request: Request,
    days: int = Query(7, ge=1, le=30, description="Lookback period in days"),
    limit: int = Query(50, ge=1, le=100, description="Max pages to return"),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get page-level emotion analysis, sorted by friction (worst pages first).

    Returns:
        - List of pages with dominant emotions
        - Session counts
        - Rage click counts
        - Average duration
        - Top behavioral signals
    """
    cutoff = datetime.now(UTC) - timedelta(days=days)

    # Get all sessions in the time window, grouped by page
    result = await db.execute(
        select(
            Session.page_url,
            func.count(Session.id).label("session_count"),
            func.avg(
                func.extract(
                    "epoch",
                    Session.ended_at - Session.started_at,
                )
            ).label("avg_duration"),
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
        )
        .group_by(Session.page_url)
    )
    page_data = result.all()

    insights = []
    for row in page_data:
        page_url = row.page_url
        session_count = row.session_count
        avg_duration = row.avg_duration or 0

        # Get emotions for sessions on this page (exclude insufficient_data)
        emotion_result = await db.execute(
            select(Session.primary_emotion, func.count().label("cnt"))
            .where(
                Session.merchant_id == merchant.id,
                Session.page_url == page_url,
                Session.started_at >= cutoff,
                Session.primary_emotion.isnot(None),
                Session.primary_emotion != "insufficient_data",
            )
            .group_by(Session.primary_emotion)
        )
        emotions = {
            r.primary_emotion: r.cnt
            for r in emotion_result.all()
        }

        # Calculate percentages
        total_emotions = sum(emotions.values()) or 1
        emotion_pct = {k: round(v / total_emotions, 4) for k, v in emotions.items()}

        dominant_emotion, dominant_pct = _get_dominant_emotion(emotion_pct)
        _, negative_pct = _get_dominant_negative(emotion_pct)

        # Count rage clicks for this page
        rage_result = await db.execute(
            select(func.count(Event.id))
            .where(
                Event.session_id.in_(
                    select(Session.id).where(
                        Session.merchant_id == merchant.id,
                        Session.page_url == page_url,
                        Session.started_at >= cutoff,
                    )
                ),
                Event.type == "rage_click",
            )
        )
        rage_clicks = rage_result.scalar() or 0

        # Determine top signals
        signals = []
        if rage_clicks > 5:
            signals.append("rage clicks")
        if negative_pct > 30:
            signals.append("negative emotions")
        if avg_duration < 10:
            signals.append("short sessions")
        elif avg_duration > 300:
            signals.append("long sessions")

        insights.append(
            PageInsightItem(
                page_url=page_url,
                session_count=session_count,
                dominant_emotion=dominant_emotion,
                dominant_emotion_pct=dominant_pct,
                rage_clicks=rage_clicks,
                avg_duration_seconds=round(avg_duration, 1),
                top_signals=signals or ["normal activity"],
            )
        )

    # Sort by dominant negative emotion % (worst first), then rage clicks
    insights.sort(
        key=lambda p: (
            -max([p.dominant_emotion_pct if p.dominant_emotion in NEGATIVE_EMOTIONS else 0, 0]),
            -p.rage_clicks,
        )
    )

    return PageInsightsResponse(
        pages=insights[:limit],
        total_pages=len(insights),
    )


@router.get("/insights/detail", response_model=PageDetailInsight, summary="Get page detail (query param)")
@limiter.limit("60/minute")
async def get_page_detail_query(
    request: Request,
    page: str = Query(..., description="Page URL to get details for"),
    days: int = Query(7, ge=1, le=30, description="Lookback period in days"),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get detailed emotion analysis for a single page using query parameter.

    This endpoint is preferred over the path-parameter version as it handles
    URLs with slashes more cleanly.
    """
    from urllib.parse import unquote, urlparse
    from sqlalchemy import or_

    page_url = unquote(page)
    cutoff = datetime.now(UTC) - timedelta(days=days)

    # DEBUG: Log what we received
    print(f"[DEBUG] Page detail request:")
    print(f"  page_url: {page_url}")
    print(f"  merchant_id: {merchant.id}")
    print(f"  cutoff: {cutoff}")
    print(f"  days: {days}")

    # Build URL matching conditions - handle full URLs, paths, and special names
    url_conditions = []

    if page_url.startswith("http"):
        # Full URL: try exact match first
        url_conditions.append(Session.page_url == page_url)
        # Also try matching by pathname (in case DB has different domain/port)
        try:
            parsed = urlparse(page_url)
            pathname = parsed.pathname
            if pathname and pathname != "/":
                # Match by pathname (works for different domains/ports)
                url_conditions.append(Session.page_url.contains(pathname))
                # Try without leading slash too (e.g., "docs" instead of "/docs")
                if pathname.startswith("/"):
                    path_without_slash = pathname[1:]
                    url_conditions.append(Session.page_url.contains(path_without_slash))
                    # Try exact pathname match
                    url_conditions.append(Session.page_url == pathname)
                    url_conditions.append(Session.page_url == path_without_slash)
        except Exception:
            pass
    else:
        # Just a pathname or "Home"
        if page_url == "Home" or page_url == "/":
            # Home page - match multiple patterns
            url_conditions.append(Session.page_url == "/")
            url_conditions.append(Session.page_url.like("%:///%"))
            url_conditions.append(Session.page_url.like("%://localhost%"))
            url_conditions.append(Session.page_url.like("%://emoratest.com%"))
            url_conditions.append(Session.page_url.like("%://emoratest.com/%"))
        else:
            # Specific pathname like "/docs" or "docs"
            url_conditions.append(Session.page_url == page_url)
            url_conditions.append(Session.page_url.like(f"%{page_url}%"))
            # Also try with leading slash
            if not page_url.startswith("/"):
                url_conditions.append(Session.page_url.contains(f"/{page_url}"))
                url_conditions.append(Session.page_url.like(f"%//{page_url}%"))
                url_conditions.append(Session.page_url == f"/{page_url}")

    # Use OR to match any of the conditions
    url_condition = or_(*url_conditions) if url_conditions else Session.page_url.contains(page_url)

    # DEBUG: Log the URL conditions being used
    print(f"[DEBUG] Page detail - Query URL: {page_url}")
    print(f"[DEBUG] Page detail - URL conditions count: {len(url_conditions)}")

    # Get session count
    count_result = await db.execute(
        select(func.count(Session.id))
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
        )
    )
    total_sessions = count_result.scalar() or 0

    # DEBUG: Log what URLs exist for this merchant
    all_urls_result = await db.execute(
        select(Session.page_url, Session.started_at)
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
        )
        .limit(10)
    )
    all_urls = all_urls_result.all()
    print(f"[DEBUG] Page detail - Found {len(all_urls)} sessions for merchant in time window:")
    for url, started in all_urls:
        print(f"  - {url} (started: {started})")
    print(f"[DEBUG] Page detail - URL conditions: {len(url_conditions)} conditions")
    print(f"[DEBUG] Page detail - Total matching sessions: {total_sessions}")

    if total_sessions == 0:
        raise HTTPException(status_code=404, detail="No data for this page")

    # Get emotion breakdown (exclude insufficient_data)
    emotion_result = await db.execute(
        select(Session.primary_emotion, func.count().label("cnt"))
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
            Session.primary_emotion.isnot(None),
            Session.primary_emotion != "insufficient_data",
        )
        .group_by(Session.primary_emotion)
    )
    emotion_rows = emotion_result.all()
    total_emotions = sum(r.cnt for r in emotion_rows) or 1
    emotion_breakdown = {
        r.primary_emotion: round(r.cnt / total_emotions * 100, 1)
        for r in emotion_rows
    }

    # Calculate trends (vs previous period)
    prev_cutoff = cutoff - timedelta(days=days)
    curr_frustration = emotion_breakdown.get("frustration", 0)

    prev_emotion_result = await db.execute(
        select(Session.primary_emotion, func.count().label("cnt"))
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= prev_cutoff,
            Session.started_at < cutoff,
            url_condition,
            Session.primary_emotion.isnot(None),
            Session.primary_emotion != "insufficient_data",
        )
        .group_by(Session.primary_emotion)
    )
    prev_emotion_rows = prev_emotion_result.all()
    total_prev = sum(r.cnt for r in prev_emotion_rows) or 1
    prev_frustration = (
        round(next((r.cnt for r in prev_emotion_rows if r.primary_emotion == "frustration"), 0) / total_prev * 100, 1)
        if prev_emotion_rows
        else 0
    )

    trend = {
        "frustration_change": round(curr_frustration - prev_frustration, 1),
    }

    # Get interactive elements (simplified - return top elements with events)
    # In production, this would query enriched events
    interactive_elements = []

    # Get recent sessions
    sessions_result = await db.execute(
        select(Session.id, Session.started_at, Session.primary_emotion, Session.emotion_confidence)
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
        )
        .order_by(desc(Session.started_at))
        .limit(5)
    )
    recent_sessions = [
        {
            "id": str(s.id),
            "started_at": s.started_at.isoformat(),
            "primary_emotion": s.primary_emotion,
            "emotion_confidence": s.emotion_confidence,
        }
    for s in sessions_result.all()
    ]

    return PageDetailInsight(
        page_url=page_url,
        total_sessions=total_sessions,
        emotion_breakdown=emotion_breakdown,
        trend=trend,
        interactive_elements=interactive_elements,
        recent_sessions=recent_sessions,
    )


@router.get(
    "/insights/{encoded_page}",
    response_model=PageDetailInsight,
    summary="Get page detail (DEPRECATED - use /insights/detail with query param)",
    deprecated=True,
)
@limiter.limit("60/minute")
async def get_page_detail(
    request: Request,
    encoded_page: str,
    days: int = Query(7, ge=1, le=30, description="Lookback period in days"),
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get detailed emotion analysis for a single page.

    DEPRECATED: This endpoint is deprecated because the path parameter approach
    has issues with URLs containing slashes. Use GET /insights/detail?page=...
    instead, which handles URLs more reliably.
    """
    from urllib.parse import unquote, urlparse
    from sqlalchemy import or_

    page_url = unquote(encoded_page)
    cutoff = datetime.now(UTC) - timedelta(days=days)

    # Handle both full URLs and pathnames (like "/signup" or "Home")
    # If page_url starts with "http", it's a full URL
    # Otherwise, it's a pathname or page name
    if not page_url.startswith("http"):
        # It's a pathname or page name - match by contains
        # "Home" maps to "/", "/signup" maps to pages containing "/signup"
        if page_url == "Home" or page_url == "/":
            page_pattern = "/"
        else:
            page_pattern = page_url
    else:
        # It's a full URL - try exact match first, then pathname matching
        try:
            parsed_target = urlparse(page_url)
            # For full URLs, try both exact match and pathname match
            # This handles cases where DB stores "http://localhost:8000/signup"
            # and we receive the same URL
        except Exception:
            page_pattern = page_url

    # Build query conditions - match by exact URL OR by pathname contains
    # This handles both: full URL in DB and pathname being passed
    url_conditions = []

    if page_url.startswith("http"):
        # Full URL: try exact match first
        url_conditions.append(Session.page_url == page_url)
        # Also try matching by pathname
        try:
            parsed = urlparse(page_url)
            pathname = parsed.pathname
            if pathname and pathname != "/":
                url_conditions.append(Session.page_url.contains(pathname))
        except Exception:
            pass
        # Handle home page URLs
        if page_url.endswith("/") or page_url.endswith(":/") or "/?" in page_url:
            url_conditions.append(Session.page_url.contains("/"))
    else:
        # Just a pathname or "Home"
        if page_pattern == "/":
            # Home page - match URLs ending with / or containing just domain
            url_conditions.append(Session.page_url == "/")
            url_conditions.append(Session.page_url.contains(":80/"))
            url_conditions.append(Session.page_url.contains(":3000/"))
            url_conditions.append(Session.page_url.contains(":8000/"))
            url_conditions.append(Session.page_url.contains("emoratest.com/"))
            url_conditions.append(Session.page_url.contains("localhost/"))
        else:
            # Specific pathname
            url_conditions.append(Session.page_url.contains(page_pattern))
            # Also try exact match in case DB stores just the pathname
            url_conditions.append(Session.page_url == page_pattern)

    # Use OR to match any of the conditions
    url_condition = or_(*url_conditions) if url_conditions else Session.page_url.contains(page_pattern)

    # Get session count
    count_result = await db.execute(
        select(func.count(Session.id))
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
        )
    )
    total_sessions = count_result.scalar() or 0

    if total_sessions == 0:
        raise HTTPException(status_code=404, detail="No data for this page")

    # Get emotion breakdown (exclude insufficient_data)
    emotion_result = await db.execute(
        select(Session.primary_emotion, func.count().label("cnt"))
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
            Session.primary_emotion.isnot(None),
            Session.primary_emotion != "insufficient_data",
        )
        .group_by(Session.primary_emotion)
    )
    emotion_rows = emotion_result.all()
    total_emotions = sum(r.cnt for r in emotion_rows) or 1
    emotion_breakdown = {
        r.primary_emotion: round(r.cnt / total_emotions * 100, 1)
        for r in emotion_rows
    }

    # Calculate trends (vs previous period)
    prev_cutoff = cutoff - timedelta(days=days)
    curr_frustration = emotion_breakdown.get("frustration", 0)

    prev_emotion_result = await db.execute(
        select(Session.primary_emotion, func.count().label("cnt"))
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= prev_cutoff,
            Session.started_at < cutoff,
            url_condition,
            Session.primary_emotion.isnot(None),
            Session.primary_emotion != "insufficient_data",
        )
        .group_by(Session.primary_emotion)
    )
    prev_emotion_rows = prev_emotion_result.all()
    total_prev = sum(r.cnt for r in prev_emotion_rows) or 1
    prev_frustration = (
        round(next((r.cnt for r in prev_emotion_rows if r.primary_emotion == "frustration"), 0) / total_prev * 100, 1)
        if prev_emotion_rows
        else 0
    )

    trend = {
        "frustration_change": round(curr_frustration - prev_frustration, 1),
    }

    # Get interactive elements (simplified - return top elements with events)
    # In production, this would query enriched events
    interactive_elements = []

    # Get recent sessions
    sessions_result = await db.execute(
        select(Session.id, Session.started_at, Session.primary_emotion, Session.emotion_confidence)
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
        )
        .order_by(desc(Session.started_at))
        .limit(5)
    )
    recent_sessions = [
        {
            "id": str(s.id),
            "started_at": s.started_at.isoformat(),
            "primary_emotion": s.primary_emotion,
            "emotion_confidence": s.emotion_confidence,
        }
        for s in sessions_result.all()
    ]

    return PageDetailInsight(
        page_url=page_url,
        total_sessions=total_sessions,
        emotion_breakdown=emotion_breakdown,
        trend=trend,
        interactive_elements=interactive_elements,
        recent_sessions=recent_sessions,
    )
