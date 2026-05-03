"""Pages API — page-level emotion analysis insights."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import Date, cast, case, desc, func, or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, Session

from app.core.auth import get_merchant_id as get_merchant_flexible
from app.core.auth import get_current_merchant
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.event import Event
from app.models.merchant import Merchant
from app.models.session import Session
from app.models.session_features import SessionFeatures
from app.services.diagnosis import DiagnosisEngine, Issue

router = APIRouter(prefix="/api/v1/pages", tags=["pages"])


# ── Schemas ─────────────────────────────────────────────────────────


class PageInsightItem(BaseModel):
    page_url: str
    session_count: int
    dominant_emotion: str
    dominant_emotion_pct: float
    avg_duration_seconds: float
    frustration_rate: float
    rage_click_count: int
    bounce_rate: float
    trend: str | None = None  # "up", "down", "stable", or None

    class Config:
        from_attributes = True


class PageInsightsResponse(BaseModel):
    pages: list[PageInsightItem]
    total_pages: int


class BehavioralSignals(BaseModel):
    avg_hesitation_score: float | None
    avg_friction_score: float | None
    rage_click_sessions: int
    avg_scroll_retreats: float | None
    avg_exit_intents: float | None


class DailyEmotionCount(BaseModel):
    date: str
    emotion: str
    count: int


class PageIssue(BaseModel):
    type: str
    severity: str  # "critical", "warning", "info"
    title: str
    description: str
    affected_percentage: float | None = None
    recommendation: str


class PageDetailInsight(BaseModel):
    page_url: str
    total_sessions: int
    frustration_rate: float
    bounce_rate: float
    rage_click_count: int
    avg_duration: float
    emotion_breakdown: dict[str, float]  # emotion -> percentage
    emotion_counts: dict[str, int]  # emotion -> count
    behavioral_signals: BehavioralSignals
    daily_emotions: list[DailyEmotionCount]  # For trend chart (last 7 days)
    issues: list[PageIssue]  # Top issues from diagnosis
    recent_sessions: list[dict]


# ── Helpers ─────────────────────────────────────────────────────────


class AsyncToSyncSessionAdapter:
    """Adapter to make AsyncSession work with synchronous DiagnosisEngine.

    The DiagnosisEngine uses synchronous SQLAlchemy Session, but our
    endpoints use AsyncSession. This adapter wraps the AsyncSession
    to provide a compatible query interface.
    """
    def __init__(self, async_session: AsyncSession):
        self._async_session = async_session

    def query(self, *args, **kwargs):
        """Return a query-like object that wraps async execute."""
        return _AsyncQueryAdapter(self._async_session, args, kwargs)


class _AsyncQueryAdapter:
    """Async query adapter for synchronous query interface."""

    def __init__(self, async_session: AsyncSession, args, kwargs):
        self._async_session = async_session
        self._args = args
        self._kwargs = kwargs
        self._filters = []
        self._joins = []
        self._group_bys = []
        self._limit_val = None
        self._label = None

    def join(self, *args):
        """Add a join."""
        self._joins.extend(args)
        return self

    def filter(self, *args):
        """Add filter conditions."""
        self._filters.extend(args)
        return self

    def group_by(self, *args):
        """Add group by clauses."""
        self._group_bys.extend(args)
        return self

    def limit(self, val):
        """Set limit."""
        self._limit_val = val
        return self

    def label(self, name):
        """Set label for aggregation."""
        self._label = name
        return self

    def first(self):
        """Execute query and return first result."""
        result = self._execute()
        return result[0] if result else None

    def scalar(self):
        """Execute query and return scalar value."""
        result = self._execute()
        if result and hasattr(result[0], "__iter__") and not isinstance(result[0], str):
            return result[0][0] if len(result[0]) == 1 else result[0]
        return result[0] if result else None

    def all(self):
        """Execute query and return all results."""
        return self._execute()

    def _execute(self):
        """Execute the async query synchronously."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self._async_execute())

    async def _async_execute(self):
        """Async execute implementation."""
        from sqlalchemy import select

        # Build the select statement
        if self._args:
            stmt = select(*self._args)
        else:
            stmt = select()

        # Add joins
        for join_arg in self._joins:
            stmt = stmt.join(join_arg)

        # Add filters
        for filt in self._filters:
            stmt = stmt.where(filt)

        # Add group by
        for group_by in self._group_bys:
            stmt = stmt.group_by(group_by)

        # Add limit
        if self._limit_val:
            stmt = stmt.limit(self._limit_val)

        # Execute
        result = await self._async_session.execute(stmt)
        return result.all()


# Map old 8 emotions to new 4 emotions for backward compatibility
EMOTION_CONSOLIDATION_MAP = {
    "frustration": "frustrated",
    "anxiety": "frustrated",
    "confusion": "confused",
    "focus": "engaged",
    "satisfaction": "engaged",
    "delight": "engaged",
    "boredom": "disengaged",
    "hesitation": "disengaged",
}

NEGATIVE_EMOTIONS = ["frustrated", "confused", "disengaged"]

ALL_EMOTIONS = ["frustrated", "confused", "engaged", "disengaged"]


def _consolidate_emotion(emotion: str) -> str:
    """Map old emotion names to new 4-emotion system."""
    return EMOTION_CONSOLIDATION_MAP.get(emotion, emotion)


def _get_dominant_emotion(emotions: dict) -> tuple[str, float]:
    """Get the dominant emotion and its percentage from emotion counts."""
    if not emotions:
        return "unknown", 0.0

    max_emotion = max(emotions.items(), key=lambda x: x[1])
    return _consolidate_emotion(max_emotion[0]), round(max_emotion[1] * 100, 1)


def _get_dominant_negative(emotions: dict) -> tuple[str, float]:
    """Get the dominant negative emotion and its percentage."""
    if not emotions:
        return "none", 0.0

    # Consolidate emotions before checking
    consolidated = {}
    for emotion, count in emotions.items():
        mapped = _consolidate_emotion(emotion)
        consolidated[mapped] = consolidated.get(mapped, 0) + count

    total = sum(consolidated.values()) or 1
    negative = {k: v for k, v in consolidated.items() if k in NEGATIVE_EMOTIONS}
    if not negative:
        return "none", 0.0

    max_emotion = max(negative.items(), key=lambda x: x[1])
    return max_emotion[0], round(max_emotion[1] / total * 100, 1)


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
    """Get page-level emotion analysis, sorted by frustration rate (worst pages first).

    Returns:
        - Frustration rate: % of sessions with primary_emotion='frustration' or 'frustrated'
        - Rage click count: sessions with rage_click_score > 0.3
        - Bounce rate: % of sessions with duration < 10 seconds
        - Trend: comparison of frustration rate vs previous period
    """
    cutoff = datetime.now(UTC) - timedelta(days=days)
    prev_cutoff = cutoff - timedelta(days=days)

    # Get all pages in the time window
    pages_result = await db.execute(
        select(Session.page_url)
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
        )
        .distinct()
    )
    all_pages = [r[0] for r in pages_result.all()]

    insights = []
    for page_url in all_pages:
        # Get session count for this page
        session_result = await db.execute(
            select(func.count(Session.id))
            .where(
                Session.merchant_id == merchant.id,
                Session.page_url == page_url,
                Session.started_at >= cutoff,
            )
        )
        session_count = session_result.scalar() or 0

        if session_count == 0:
            continue

        # Get emotion breakdown for frustration rate
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
        emotions = {r.primary_emotion: r.cnt for r in emotion_result.all()}

        # Calculate frustration rate (consolidated emotions)
        frustrated_count = (
            emotions.get("frustration", 0) +
            emotions.get("frustrated", 0) +
            emotions.get("anxiety", 0)
        )
        frustration_rate = round(frustrated_count / session_count * 100, 1) if session_count else 0

        # Get dominant emotion
        total_emotions = sum(emotions.values()) or 1
        emotion_pct = {k: round(v / total_emotions, 4) for k, v in emotions.items()}
        dominant_emotion, dominant_pct = _get_dominant_emotion(emotion_pct)

        # Calculate average duration
        duration_result = await db.execute(
            select(
                func.avg(
                    func.extract("epoch", Session.ended_at - Session.started_at)
                )
            )
            .where(
                Session.merchant_id == merchant.id,
                Session.page_url == page_url,
                Session.started_at >= cutoff,
                Session.ended_at.isnot(None),
            )
        )
        avg_duration = duration_result.scalar() or 0

        # Count rage click sessions (rage_click_score > 0.3)
        rage_result = await db.execute(
            select(func.count(Session.id))
            .join(SessionFeatures, SessionFeatures.session_id == Session.id)
            .where(
                Session.merchant_id == merchant.id,
                Session.page_url == page_url,
                Session.started_at >= cutoff,
                SessionFeatures.rage_click_score > 0.3,
            )
        )
        rage_click_count = rage_result.scalar() or 0

        # Count bounce sessions (duration < 10 seconds)
        bounce_result = await db.execute(
            select(func.count(Session.id))
            .where(
                Session.merchant_id == merchant.id,
                Session.page_url == page_url,
                Session.started_at >= cutoff,
                Session.ended_at.isnot(None),
                func.extract("epoch", Session.ended_at - Session.started_at) < 10,
            )
        )
        bounce_count = bounce_result.scalar() or 0
        bounce_rate = round(bounce_count / session_count * 100, 1) if session_count else 0

        # Calculate trend (compare frustration rate vs previous period)
        prev_emotion_result = await db.execute(
            select(Session.primary_emotion, func.count().label("cnt"))
            .where(
                Session.merchant_id == merchant.id,
                Session.page_url == page_url,
                Session.started_at >= prev_cutoff,
                Session.started_at < cutoff,
                Session.primary_emotion.isnot(None),
                Session.primary_emotion != "insufficient_data",
            )
            .group_by(Session.primary_emotion)
        )
        prev_emotions = {r.primary_emotion: r.cnt for r in prev_emotion_result.all()}
        prev_session_count = sum(prev_emotions.values()) or 1

        prev_frustrated_count = (
            prev_emotions.get("frustration", 0) +
            prev_emotions.get("frustrated", 0) +
            prev_emotions.get("anxiety", 0)
        )
        prev_frustration_rate = round(prev_frustrated_count / prev_session_count * 100, 1) if prev_session_count else 0

        # Determine trend direction
        if abs(frustration_rate - prev_frustration_rate) < 5:
            trend = "stable"
        elif frustration_rate > prev_frustration_rate:
            trend = "up"
        else:
            trend = "down"

        insights.append(
            PageInsightItem(
                page_url=page_url,
                session_count=session_count,
                dominant_emotion=dominant_emotion,
                dominant_emotion_pct=dominant_pct,
                avg_duration_seconds=round(avg_duration, 1),
                frustration_rate=frustration_rate,
                rage_click_count=rage_click_count,
                bounce_rate=bounce_rate,
                trend=trend,
            )
        )

    # Sort by frustration rate (highest first), then rage click count
    insights.sort(key=lambda p: (-p.frustration_rate, -p.rage_click_count))

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

    Returns summary stats, emotion breakdown with counts, behavioral signals,
    daily emotion trends, detected issues, and recent sessions.
    """
    from urllib.parse import unquote, urlparse

    page_url = unquote(page)
    cutoff = datetime.now(UTC) - timedelta(days=days)

    # Build URL matching conditions - handle full URLs, paths, and special names
    url_conditions = []

    if page_url.startswith("http"):
        url_conditions.append(Session.page_url == page_url)
        try:
            parsed = urlparse(page_url)
            pathname = parsed.pathname
            if pathname and pathname != "/":
                url_conditions.append(Session.page_url.contains(pathname))
                if pathname.startswith("/"):
                    path_without_slash = pathname[1:]
                    url_conditions.append(Session.page_url.contains(path_without_slash))
                    url_conditions.append(Session.page_url == pathname)
                    url_conditions.append(Session.page_url == path_without_slash)
        except Exception:
            pass
    else:
        if page_url == "Home" or page_url == "/":
            url_conditions.append(Session.page_url == "/")
            url_conditions.append(Session.page_url.like("%:///%"))
            url_conditions.append(Session.page_url.like("%://localhost%"))
            url_conditions.append(Session.page_url.like("%://emoratest.com%"))
            url_conditions.append(Session.page_url.like("%://emoratest.com/%"))
        else:
            url_conditions.append(Session.page_url == page_url)
            url_conditions.append(Session.page_url.like(f"%{page_url}%"))
            if not page_url.startswith("/"):
                url_conditions.append(Session.page_url.contains(f"/{page_url}"))
                url_conditions.append(Session.page_url.like(f"%//{page_url}%"))
                url_conditions.append(Session.page_url == f"/{page_url}")

    url_condition = or_(*url_conditions) if url_conditions else Session.page_url.contains(page_url)

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

    # Get emotion breakdown with counts
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

    # Consolidate old emotion names to new 4-emotion system
    emotion_breakdown: dict[str, float] = {}
    emotion_counts: dict[str, int] = {}

    for r in emotion_rows:
        consolidated = _consolidate_emotion(r.primary_emotion)
        emotion_breakdown[consolidated] = emotion_breakdown.get(consolidated, 0) + round(r.cnt / total_emotions * 100, 1)
        emotion_counts[consolidated] = emotion_counts.get(consolidated, 0) + r.cnt

    # Round percentages properly after consolidation
    for key in emotion_breakdown:
        emotion_breakdown[key] = round(emotion_breakdown[key], 1)

    # Calculate frustration rate (consolidated)
    frustrated_count = (
        emotion_counts.get("frustration", 0) +
        emotion_counts.get("frustrated", 0) +
        emotion_counts.get("anxiety", 0)
    )
    frustration_rate = round(frustrated_count / total_sessions * 100, 1) if total_sessions else 0

    # Calculate bounce rate (sessions < 10 seconds)
    bounce_result = await db.execute(
        select(func.count(Session.id))
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
            Session.ended_at.isnot(None),
            func.extract("epoch", Session.ended_at - Session.started_at) < 10,
        )
    )
    bounce_count = bounce_result.scalar() or 0
    bounce_rate = round(bounce_count / total_sessions * 100, 1) if total_sessions else 0

    # Count rage click sessions
    rage_result = await db.execute(
        select(func.count(Session.id))
        .join(SessionFeatures, SessionFeatures.session_id == Session.id)
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
            SessionFeatures.rage_click_score > 0.3,
        )
    )
    rage_click_count = rage_result.scalar() or 0

    # Calculate average duration
    duration_result = await db.execute(
        select(
            func.avg(func.extract("epoch", Session.ended_at - Session.started_at))
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
            Session.ended_at.isnot(None),
        )
    )
    avg_duration = duration_result.scalar() or 0

    # Get behavioral signals from session_features and session
    features_result = await db.execute(
        select(
            func.avg(SessionFeatures.hesitation_score).label("avg_hesitation"),
            func.avg(Session.friction_score).label("avg_friction"),
            func.avg(SessionFeatures.scroll_retreat_count).label("avg_scroll_retreats"),
            func.avg(SessionFeatures.exit_intent_count).label("avg_exit_intents"),
        )
        .join(Session, SessionFeatures.session_id == Session.id)
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
        )
    )
    features_row = features_result.first()

    behavioral_signals = BehavioralSignals(
        avg_hesitation_score=round(features_row.avg_hesitation, 3) if features_row and features_row.avg_hesitation else None,
        avg_friction_score=round(features_row.avg_friction, 3) if features_row and features_row.avg_friction else None,
        rage_click_sessions=rage_click_count,
        avg_scroll_retreats=round(features_row.avg_scroll_retreats, 1) if features_row and features_row.avg_scroll_retreats else None,
        avg_exit_intents=round(features_row.avg_exit_intents, 1) if features_row and features_row.avg_exit_intents else None,
    )

    # Get daily emotion counts for trend chart (last 7 days)
    daily_emotions_result = await db.execute(
        select(
            cast(Session.started_at, Date).label("date"),
            Session.primary_emotion,
            func.count().label("cnt")
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
            Session.primary_emotion.isnot(None),
            Session.primary_emotion != "insufficient_data",
        )
        .group_by(cast(Session.started_at, Date), Session.primary_emotion)
        .order_by(cast(Session.started_at, Date))
    )

    # Consolidate emotions for daily trend chart
    daily_emotions_consolidated: dict[str, dict[str, int]] = {}
    for row in daily_emotions_result.all():
        date_str = str(row.date)
        consolidated = _consolidate_emotion(row.primary_emotion)
        if date_str not in daily_emotions_consolidated:
            daily_emotions_consolidated[date_str] = {}
        daily_emotions_consolidated[date_str][consolidated] = daily_emotions_consolidated[date_str].get(consolidated, 0) + row.cnt

    daily_emotions = [
        DailyEmotionCount(
            date=date,
            emotion=emotion,
            count=count
        )
        for date, emotions in daily_emotions_consolidated.items()
        for emotion, count in emotions.items()
    ]

    # Get issues from diagnosis engine
    # Note: Using simplified approach - call the diagnosis engine's detection logic directly
    issues = []

    # Detect rage click issues
    rage_percentage = (rage_click_count / total_sessions * 100) if total_sessions else 0
    if rage_percentage >= 15:
        issues.append(PageIssue(
            type="rage_click_cluster",
            severity="critical" if rage_percentage >= 30 else "warning",
            title=f"Rage clicks detected on this page",
            description=f"{rage_percentage:.1f}% of sessions ({rage_click_count} sessions) show rage clicking behavior.",
            affected_percentage=round(rage_percentage, 1),
            recommendation="Check for broken buttons, slow-loading elements, or misleading clickable elements.",
        ))

    # Detect high bounce issues
    if bounce_rate >= 25:
        issues.append(PageIssue(
            type="high_bounce",
            severity="critical" if bounce_rate >= 50 else "warning",
            title=f"High bounce rate on this page",
            description=f"{bounce_rate:.1f}% of visitors leave within 10 seconds ({bounce_count} of {total_sessions} sessions).",
            affected_percentage=round(bounce_rate, 1),
            recommendation="Review page load speed, above-the-fold content, and whether the page matches user expectations.",
        ))

    # Detect frustration issues
    if frustration_rate >= 20:
        issues.append(PageIssue(
            type="high_frustration",
            severity="critical" if frustration_rate >= 40 else "warning",
            title=f"High frustration rate on this page",
            description=f"{frustration_rate:.1f}% of sessions show frustrated emotions.",
            affected_percentage=round(frustration_rate, 1),
            recommendation="Investigate usability issues, confusing elements, or technical problems on this page.",
        ))

    # Get recent sessions with enhanced data
    sessions_result = await db.execute(
        select(
            Session.id,
            Session.started_at,
            Session.primary_emotion,
            Session.emotion_confidence,
            Session.outcome,
            Session.friction_score,
            func.extract("epoch", Session.ended_at - Session.started_at).label("duration")
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
        )
        .order_by(desc(Session.started_at))
        .limit(10)
    )
    recent_sessions = []
    for s in sessions_result.all():
        duration = s.duration if s.duration else None
        recent_sessions.append({
            "id": str(s.id),
            "started_at": s.started_at.isoformat(),
            "primary_emotion": s.primary_emotion,
            "emotion_confidence": s.emotion_confidence,
            "outcome": s.outcome,
            "friction_score": round(s.friction_score, 2) if s.friction_score else None,
            "duration_seconds": round(duration) if duration else None,
        })

    return PageDetailInsight(
        page_url=page_url,
        total_sessions=total_sessions,
        frustration_rate=frustration_rate,
        bounce_rate=bounce_rate,
        rage_click_count=rage_click_count,
        avg_duration=round(avg_duration, 1),
        emotion_breakdown=emotion_breakdown,
        emotion_counts=emotion_counts,
        behavioral_signals=behavioral_signals,
        daily_emotions=daily_emotions,
        issues=issues,
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

    page_url = unquote(encoded_page)
    cutoff = datetime.now(UTC) - timedelta(days=days)

    # Build URL matching conditions - handle full URLs, paths, and special names
    url_conditions = []

    if page_url.startswith("http"):
        url_conditions.append(Session.page_url == page_url)
        try:
            parsed = urlparse(page_url)
            pathname = parsed.pathname
            if pathname and pathname != "/":
                url_conditions.append(Session.page_url.contains(pathname))
                if pathname.startswith("/"):
                    path_without_slash = pathname[1:]
                    url_conditions.append(Session.page_url.contains(path_without_slash))
                    url_conditions.append(Session.page_url == pathname)
                    url_conditions.append(Session.page_url == path_without_slash)
        except Exception:
            pass
    else:
        if page_url == "Home" or page_url == "/":
            url_conditions.append(Session.page_url == "/")
            url_conditions.append(Session.page_url.like("%:///%"))
            url_conditions.append(Session.page_url.like("%://localhost%"))
            url_conditions.append(Session.page_url.like("%://emoratest.com%"))
            url_conditions.append(Session.page_url.like("%://emoratest.com/%"))
        else:
            url_conditions.append(Session.page_url == page_url)
            url_conditions.append(Session.page_url.like(f"%{page_url}%"))
            if not page_url.startswith("/"):
                url_conditions.append(Session.page_url.contains(f"/{page_url}"))
                url_conditions.append(Session.page_url.like(f"%//{page_url}%"))
                url_conditions.append(Session.page_url == f"/{page_url}")

    url_condition = or_(*url_conditions) if url_conditions else Session.page_url.contains(page_url)

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

    # Get emotion breakdown with counts
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

    # Consolidate old emotion names to new 4-emotion system
    emotion_breakdown: dict[str, float] = {}
    emotion_counts: dict[str, int] = {}

    for r in emotion_rows:
        consolidated = _consolidate_emotion(r.primary_emotion)
        emotion_breakdown[consolidated] = emotion_breakdown.get(consolidated, 0) + round(r.cnt / total_emotions * 100, 1)
        emotion_counts[consolidated] = emotion_counts.get(consolidated, 0) + r.cnt

    # Round percentages properly after consolidation
    for key in emotion_breakdown:
        emotion_breakdown[key] = round(emotion_breakdown[key], 1)

    # Calculate frustration rate (consolidated)
    frustrated_count = (
        emotion_counts.get("frustration", 0) +
        emotion_counts.get("frustrated", 0) +
        emotion_counts.get("anxiety", 0)
    )
    frustration_rate = round(frustrated_count / total_sessions * 100, 1) if total_sessions else 0

    # Calculate bounce rate (sessions < 10 seconds)
    bounce_result = await db.execute(
        select(func.count(Session.id))
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
            Session.ended_at.isnot(None),
            func.extract("epoch", Session.ended_at - Session.started_at) < 10,
        )
    )
    bounce_count = bounce_result.scalar() or 0
    bounce_rate = round(bounce_count / total_sessions * 100, 1) if total_sessions else 0

    # Count rage click sessions
    rage_result = await db.execute(
        select(func.count(Session.id))
        .join(SessionFeatures, SessionFeatures.session_id == Session.id)
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
            SessionFeatures.rage_click_score > 0.3,
        )
    )
    rage_click_count = rage_result.scalar() or 0

    # Calculate average duration
    duration_result = await db.execute(
        select(
            func.avg(func.extract("epoch", Session.ended_at - Session.started_at))
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
            Session.ended_at.isnot(None),
        )
    )
    avg_duration = duration_result.scalar() or 0

    # Get behavioral signals from session_features and session
    features_result = await db.execute(
        select(
            func.avg(SessionFeatures.hesitation_score).label("avg_hesitation"),
            func.avg(Session.friction_score).label("avg_friction"),
            func.avg(SessionFeatures.scroll_retreat_count).label("avg_scroll_retreats"),
            func.avg(SessionFeatures.exit_intent_count).label("avg_exit_intents"),
        )
        .join(Session, SessionFeatures.session_id == Session.id)
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
        )
    )
    features_row = features_result.first()

    behavioral_signals = BehavioralSignals(
        avg_hesitation_score=round(features_row.avg_hesitation, 3) if features_row and features_row.avg_hesitation else None,
        avg_friction_score=round(features_row.avg_friction, 3) if features_row and features_row.avg_friction else None,
        rage_click_sessions=rage_click_count,
        avg_scroll_retreats=round(features_row.avg_scroll_retreats, 1) if features_row and features_row.avg_scroll_retreats else None,
        avg_exit_intents=round(features_row.avg_exit_intents, 1) if features_row and features_row.avg_exit_intents else None,
    )

    # Get daily emotion counts for trend chart
    daily_emotions_result = await db.execute(
        select(
            cast(Session.started_at, Date).label("date"),
            Session.primary_emotion,
            func.count().label("cnt")
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
            Session.primary_emotion.isnot(None),
            Session.primary_emotion != "insufficient_data",
        )
        .group_by(cast(Session.started_at, Date), Session.primary_emotion)
        .order_by(cast(Session.started_at, Date))
    )
    daily_emotions = [
        DailyEmotionCount(
            date=str(row.date),
            emotion=row.primary_emotion,
            count=row.cnt
        )
        for row in daily_emotions_result.all()
    ]

    # Get issues from diagnosis engine (simplified)
    issues = []

    rage_percentage = (rage_click_count / total_sessions * 100) if total_sessions else 0
    if rage_percentage >= 15:
        issues.append(PageIssue(
            type="rage_click_cluster",
            severity="critical" if rage_percentage >= 30 else "warning",
            title=f"Rage clicks detected on this page",
            description=f"{rage_percentage:.1f}% of sessions show rage clicking behavior.",
            affected_percentage=round(rage_percentage, 1),
            recommendation="Check for broken buttons, slow-loading elements, or misleading clickable elements.",
        ))

    if bounce_rate >= 25:
        issues.append(PageIssue(
            type="high_bounce",
            severity="critical" if bounce_rate >= 50 else "warning",
            title=f"High bounce rate on this page",
            description=f"{bounce_rate:.1f}% of visitors leave within 10 seconds.",
            affected_percentage=round(bounce_rate, 1),
            recommendation="Review page load speed and above-the-fold content.",
        ))

    if frustration_rate >= 20:
        issues.append(PageIssue(
            type="high_frustration",
            severity="critical" if frustration_rate >= 40 else "warning",
            title=f"High frustration rate on this page",
            description=f"{frustration_rate:.1f}% of sessions show frustrated emotions.",
            affected_percentage=round(frustration_rate, 1),
            recommendation="Investigate usability issues or technical problems.",
        ))

    # Get recent sessions with enhanced data
    sessions_result = await db.execute(
        select(
            Session.id,
            Session.started_at,
            Session.primary_emotion,
            Session.emotion_confidence,
            Session.outcome,
            Session.friction_score,
            func.extract("epoch", Session.ended_at - Session.started_at).label("duration")
        )
        .where(
            Session.merchant_id == merchant.id,
            Session.started_at >= cutoff,
            url_condition,
        )
        .order_by(desc(Session.started_at))
        .limit(10)
    )
    recent_sessions = []
    for s in sessions_result.all():
        duration = s.duration if s.duration else None
        recent_sessions.append({
            "id": str(s.id),
            "started_at": s.started_at.isoformat(),
            "primary_emotion": s.primary_emotion,
            "emotion_confidence": s.emotion_confidence,
            "outcome": s.outcome,
            "friction_score": round(s.friction_score, 2) if s.friction_score else None,
            "duration_seconds": round(duration) if duration else None,
        })

    return PageDetailInsight(
        page_url=page_url,
        total_sessions=total_sessions,
        frustration_rate=frustration_rate,
        bounce_rate=bounce_rate,
        rage_click_count=rage_click_count,
        avg_duration=round(avg_duration, 1),
        emotion_breakdown=emotion_breakdown,
        emotion_counts=emotion_counts,
        behavioral_signals=behavioral_signals,
        daily_emotions=daily_emotions,
        issues=issues,
        recent_sessions=recent_sessions,
    )
