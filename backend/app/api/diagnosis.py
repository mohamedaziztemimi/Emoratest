"""Diagnosis API — turns behavior signals into actionable fixes.

This is the CORE product layer — it transforms raw behavioral data
(rage clicks, hesitation, drop-offs) into:
1. Clear problem statements
2. Supporting evidence
3. Root cause explanations
4. Concrete action recommendations
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.auth import get_current_merchant
from app.models.session import Session
from app.models.session_features import SessionFeatures
from app.models.merchant import Merchant
from sqlalchemy import func, desc, and_, Integer, cast
from sqlalchemy.orm import Session as DBSession

router = APIRouter(prefix="/api/v1/diagnosis", tags=["diagnosis"])


# ─────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────


class ProblemSummary(BaseModel):
    """The core problem statement — what's wrong and how bad is it."""

    title: str = Field(..., description="Plain language problem statement")
    page_url: str = Field(..., description="Page where problem occurs")
    page_name: str = Field(..., description="Human-readable page name")
    affected_users_pct: float = Field(..., description="% of users affected")
    severity: str = Field(..., description="high | medium | low")
    estimated_lost_revenue: str | None = Field(None, description="Estimated impact in $")


class EvidenceItem(BaseModel):
    """Specific behavioral evidence supporting the diagnosis."""

    type: str = Field(..., description="rage_clicks | hesitation | drop_off | session_replay")
    value: float | int | str = Field(..., description="Measured value")
    label: str = Field(..., description="Human-readable label")
    element: str | None = Field(None, description="Element selector if applicable")
    session_ids: list[str] = Field(default_factory=list, description="Example sessions")


class RootCause(BaseModel):
    """Why this problem exists — explained in plain language."""

    primary_cause: str = Field(..., description="Main reason")
    explanation: str = Field(..., description="Plain language explanation")
    contributing_factors: list[str] = Field(default_factory=list)


class ActionItem(BaseModel):
    """Concrete fix the user can apply."""

    title: str = Field(..., description="Action title")
    description: str = Field(..., description="What to do")
    type: str = Field(..., description="edit_element | ab_test | copy_change | technical_fix")
    link: str | None = Field(None, description="Direct link to take action")


class DiagnosisResponse(BaseModel):
    """Complete diagnosis for a single top problem."""

    summary: ProblemSummary
    evidence: list[EvidenceItem]
    root_cause: RootCause
    actions: list[ActionItem]
    supporting_charts: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class IssueListItem(BaseModel):
    """Condensed issue for the list view."""

    id: str = Field(..., description="Unique issue identifier")
    title: str = Field(..., description="Brief problem statement")
    page_url: str = Field(..., description="Affected page")
    affected_users: int = Field(..., description="Number of users affected")
    severity: str = Field(..., description="high | medium | low")


class IssuesListResponse(BaseModel):
    """List of all detected issues, prioritized."""

    issues: list[IssueListItem]
    total_issues: int
    high_severity_count: int


# ─────────────────────────────────────────────────────────────────────────
# Derived Insights Service
# ─────────────────────────────────────────────────────────────────────────


class DiagnosisService:
    """Transforms behavioral signals into actionable insights.

    This is where the product logic lives — not in ML, but in how we
    interpret signals to tell users what to fix.
    """

    # Severity thresholds
    RAGE_CLICK_HIGH = 0.3
    RAGE_CLICK_MEDIUM = 0.15
    HESITATION_HIGH = 0.5
    HESITATION_MEDIUM = 0.3
    SCROLL_RETREAT_HIGH = 4
    DROP_OFF_HIGH = 0.4
    DROP_OFF_MEDIUM = 0.25

    @staticmethod
    def _extract_page_name(url: str) -> str:
        """Extract human-readable page name from URL."""
        try:
            from urllib.parse import urlparse
            path = urlparse(url).path
            parts = [p for p in path.split("/") if p and not p.isdigit()]
            if parts:
                return " ".join(p.replace("-", " ").replace("_", " ").title() for p in parts[-2:])
            return "Page"
        except Exception:
            return "Page"

    @staticmethod
    def _get_severity(
        rage_click: float | None,
        hesitation: float | None,
        drop_off: float | None,
        scroll_retreat: int | None,
    ) -> str:
        """Calculate overall severity from signals."""
        high_indicators = 0
        medium_indicators = 0

        if rage_click and rage_click >= DiagnosisService.RAGE_CLICK_HIGH:
            high_indicators += 1
        elif rage_click and rage_click >= DiagnosisService.RAGE_CLICK_MEDIUM:
            medium_indicators += 1

        if hesitation and hesitation >= DiagnosisService.HESITATION_HIGH:
            high_indicators += 1
        elif hesitation and hesitation >= DiagnosisService.HESITATION_MEDIUM:
            medium_indicators += 1

        if drop_off and drop_off >= DiagnosisService.DROP_OFF_HIGH:
            high_indicators += 1
        elif drop_off and drop_off >= DiagnosisService.DROP_OFF_MEDIUM:
            medium_indicators += 1

        if scroll_retreat and scroll_retreat >= DiagnosisService.SCROLL_RETREAT_HIGH:
            high_indicators += 1

        if high_indicators >= 2:
            return "high"
        elif high_indicators >= 1 or medium_indicators >= 2:
            return "medium"
        return "low"

    @staticmethod
    def _diagnose_rage_clicks(
        avg_rage: float, page_url: str, affected_sessions: list[str]
    ) -> tuple[ProblemSummary, RootCause, list[ActionItem]]:
        """Diagnose rage click pattern."""

        summary = ProblemSummary(
            title="Users are clicking furiously on broken elements",
            page_url=page_url,
            page_name=DiagnosisService._extract_page_name(page_url),
            affected_users_pct=round(avg_rage * 100, 1),
            severity="high" if avg_rage >= DiagnosisService.RAGE_CLICK_HIGH else "medium",
            estimated_lost_revenue=None,
        )

        root_cause = RootCause(
            primary_cause="Element appears clickable but doesn't respond",
            explanation=(
                "Users are rapidly clicking the same element because they expect "
                "an action that isn't happening. This usually means: the button "
                "looks clickable but isn't, it's blocked by an overlay, or the "
                "response is too slow."
            ),
            contributing_factors=[
                "Possible invisible overlay blocking clicks",
                "Button may have no click handler",
                "Response time > 2 seconds causing double-clicks",
            ],
        )

        actions = [
            ActionItem(
                title="Test the suspected element",
                description="Click on all buttons and links to verify they respond",
                type="edit_element",
                link=f"/dashboard/editor?url={page_url}",
            ),
            ActionItem(
                title="Create A/B test to fix",
                description="Test a version with faster response or clearer visual feedback",
                type="ab_test",
                link="/dashboard/experiments?template=fix-element",
            ),
        ]

        return summary, root_cause, actions

    @staticmethod
    def _diagnose_hesitation(
        avg_hesitation: float, page_url: str, drop_off_rate: float | None
    ) -> tuple[ProblemSummary, RootCause, list[ActionItem]]:
        """Diagnose hesitation pattern."""

        summary = ProblemSummary(
            title="Users are pausing and unsure what to do",
            page_url=page_url,
            page_name=DiagnosisService._extract_page_name(page_url),
            affected_users_pct=round(min(avg_hesitation * 80, 95), 1),
            severity="high" if avg_hesitation >= DiagnosisService.HESITATION_HIGH else "medium",
        )

        root_cause = RootCause(
            primary_cause="Decision paralysis or unclear next step",
            explanation=(
                "Users are spending extra time hovering between elements or "
                "re-reading content. This suggests they're uncertain about "
                "what action to take or don't trust the information provided."
            ),
            contributing_factors=[
                "Too many options presented at once",
                "Unclear value proposition",
                "Missing trust signals (reviews, guarantees)",
                "Confusing form or checkout flow",
            ],
        )

        actions = [
            ActionItem(
                title="Simplify the page layout",
                description="Reduce options and highlight one primary call-to-action",
                type="edit_element",
                link=f"/dashboard/editor?url={page_url}",
            ),
            ActionItem(
                title="Add social proof elements",
                description="Test adding testimonials, reviews, or trust badges",
                type="ab_test",
                link="/dashboard/experiments?template=add-social-proof",
            ),
        ]

        return summary, root_cause, actions

    @staticmethod
    def _diagnose_drop_off(
        drop_off: float, page_url: str, primary_emotion: str | None
    ) -> tuple[ProblemSummary, RootCause, list[ActionItem]]:
        """Diagnose drop-off pattern."""

        summary = ProblemSummary(
            title=f"Users are abandoning at {DiagnosisService._extract_page_name(page_url)}",
            page_url=page_url,
            page_name=DiagnosisService._extract_page_name(page_url),
            affected_users_pct=round(drop_off * 100, 1),
            severity="high" if drop_off >= DiagnosisService.DROP_OFF_HIGH else "medium",
        )

        emotion_hints = {
            "frustration": "Users are annoyed by barriers like forms, errors, or slow loading",
            "confusion": "Users don't understand what to do next",
            "anxiety": "Users are concerned about price, commitment, or trust",
            "hesitation": "Users are unsure if they should proceed",
        }

        explanation = emotion_hints.get(
            primary_emotion or "",
            "Users are leaving without completing the desired action",
        )

        root_cause = RootCause(
            primary_cause="Process friction or lack of motivation",
            explanation=explanation,
            contributing_factors=[
                f"Primary emotion detected: {primary_emotion or 'unknown'}",
                "Form may be too long or complex",
                "Pricing or commitment unclear",
                "Technical issues (errors, slow load)",
            ],
        )

        actions = [
            ActionItem(
                title="Reduce form fields",
                description="Test a shorter form or progress indicator",
                type="ab_test",
                link="/dashboard/experiments?template=shorten-form",
            ),
            ActionItem(
                title="Add exit-intent offer",
                description="Present a discount or alternative when users try to leave",
                type="ab_test",
                link="/dashboard/interventions",
            ),
        ]

        return summary, root_cause, actions


def _fetch_page_aggregates(
    db: DBSession, merchant_id: str, hours: int = 24
) -> list[dict[str, Any]]:
    """Aggregate behavioral signals by page."""

    since = datetime.utcnow() - timedelta(hours=hours)

    query = (
        db.query(
            Session.page_url,
            func.count(Session.id).label("total_sessions"),
            func.avg(SessionFeatures.rage_click_score).label("avg_rage"),
            func.avg(SessionFeatures.hesitation_score).label("avg_hesitation"),
            func.avg(SessionFeatures.scroll_retreat_count).label("avg_scroll_retreat"),
            func.avg(SessionFeatures.exit_intent_count).label("avg_exit_intent"),
            func.avg(SessionFeatures.checkout_hesitation_s).label("avg_checkout_hesitation"),
            func.avg(Session.friction_score).label("avg_friction"),
            func.avg(
                cast(Session.outcome == "abandon", Integer)
            ).label("abandon_rate"),
            func.max(Session.primary_emotion).label("top_emotion"),  # Simplified: use max as proxy
        )
        .join(SessionFeatures, Session.id == SessionFeatures.session_id)
        .filter(
            and_(
                Session.merchant_id == merchant_id,
                Session.started_at >= since,
            )
        )
        .group_by(Session.page_url)
        .having(func.count(Session.id) >= 1)  # Lower threshold - show data even with 1 session
        .order_by(desc("avg_rage"), desc("avg_hesitation"), desc("abandon_rate"))
        .limit(10)
    )

    results = []
    for row in query.all():
        results.append({
            "page_url": row.page_url,
            "total_sessions": row.total_sessions,
            "avg_rage": float(row.avg_rage) if row.avg_rage else 0,
            "avg_hesitation": float(row.avg_hesitation) if row.avg_hesitation else 0,
            "avg_scroll_retreat": float(row.avg_scroll_retreat) if row.avg_scroll_retreat else 0,
            "avg_exit_intent": float(row.avg_exit_intent) if row.avg_exit_intent else 0,
            "avg_checkout_hesitation": float(row.avg_checkout_hesitation) if row.avg_checkout_hesitation else 0,
            "avg_friction": float(row.avg_friction) if row.avg_friction else 0,
            "abandon_rate": float(row.abandon_rate) if row.abandon_rate else 0,
            "top_emotion": row.top_emotion,
        })

    return results


def _get_affected_sessions(
    db: DBSession, merchant_id: str, page_url: str, signal_type: str, limit: int = 5
) -> list[str]:
    """Get example session IDs showing the problematic behavior."""

    since = datetime.utcnow() - timedelta(hours=72)

    signal_column_map = {
        "rage": SessionFeatures.rage_click_score,
        "hesitation": SessionFeatures.hesitation_score,
        "scroll_retreat": SessionFeatures.scroll_retreat_count,
    }

    signal_col = signal_column_map.get(signal_type, SessionFeatures.rage_click_score)

    query = (
        db.query(Session.id)
        .join(SessionFeatures, Session.id == SessionFeatures.session_id)
        .filter(
            and_(
                Session.merchant_id == merchant_id,
                Session.page_url == page_url,
                Session.started_at >= since,
                signal_col.isnot(None),
            )
        )
        .order_by(desc(signal_col))
        .limit(limit)
    )

    return [str(row[0]) for row in query.all()]


@router.get(
    "/primary",
    response_model=DiagnosisResponse,
    summary="Get primary problem diagnosis",
)
@limiter.limit("60/minute")
async def get_primary_diagnosis(
    request: Request,
    db: DBSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
    hours: int = Query(default=24, ge=1, le=168, description="Lookback period in hours"),
):
    """Returns the single most critical problem with full diagnosis.

    This is the main entry point for the diagnosis page. It identifies
    the top issue and provides:
    - Clear problem statement
    - Supporting evidence (rage clicks, hesitation, sessions)
    - Root cause explanation
    - Concrete action items

    Uses JWT authentication for merchant identification.
    """

    aggregates = _fetch_page_aggregates(db, merchant.id, hours)

    # Get total session count even if no aggregates (for display)
    total_sessions_result = db.query(func.count(Session.id)).filter(
        Session.merchant_id == merchant.id,
        Session.started_at >= datetime.utcnow() - timedelta(hours=hours),
    ).scalar() or 0

    # DEBUG: Log diagnosis state
    print(f"[DEBUG] Diagnosis: merchant={merchant.id}, hours={hours}")
    print(f"[DEBUG] Diagnosis: total_sessions={total_sessions_result}, aggregates_count={len(aggregates) if aggregates else 0}")

    # Check if sessions have features (helpful for debugging)
    from app.models.session_features import SessionFeatures
    features_count = db.query(func.count(SessionFeatures.id)).join(
        Session, Session.id == SessionFeatures.session_id
    ).filter(
        Session.merchant_id == merchant.id,
        Session.started_at >= datetime.utcnow() - timedelta(hours=hours),
    ).scalar() or 0
    print(f"[DEBUG] Diagnosis: sessions_with_features={features_count}")

    if not aggregates:
        # Return neutral "no issues" state with actual session count
        return DiagnosisResponse(
            summary=ProblemSummary(
                title="No critical issues detected",
                page_url="/",
                page_name="Overview",
                affected_users_pct=0,
                severity="low",
            ),
            evidence=[],
            root_cause=RootCause(
                primary_cause="System is healthy",
                explanation="User behavior appears normal. Continue monitoring.",
            ),
            actions=[
                ActionItem(
                    title="Review your sessions",
                    description=f"View all {total_sessions_result} sessions to understand user behavior",
                    type="edit_element",
                    link="/dashboard/sessions",
                )
            ],
            supporting_charts={
                "page_stats": {
                    "total_sessions": total_sessions_result,
                    "avg_friction": None,
                    "top_emotion": None,
                }
            },
        )

    # Find the most severe issue
    for page in aggregates:
        severity = DiagnosisService._get_severity(
            page["avg_rage"],
            page["avg_hesitation"],
            page["abandon_rate"],
            int(page["avg_scroll_retreat"]),
        )
        page["severity"] = severity

    aggregates.sort(key=lambda p: (
        0 if p["severity"] == "high" else 1 if p["severity"] == "medium" else 2,
        -p["avg_rage"],
        -p["abandon_rate"],
    ))

    top = aggregates[0]
    page_url = top["page_url"]

    # Diagnose based on dominant signal
    if top["avg_rage"] >= DiagnosisService.RAGE_CLICK_MEDIUM:
        summary, root_cause, actions = DiagnosisService._diagnose_rage_clicks(
            top["avg_rage"], page_url, []
        )
    elif top["avg_hesitation"] >= DiagnosisService.HESITATION_MEDIUM:
        summary, root_cause, actions = DiagnosisService._diagnose_hesitation(
            top["avg_hesitation"], page_url, top["abandon_rate"]
        )
    else:
        summary, root_cause, actions = DiagnosisService._diagnose_drop_off(
            top["abandon_rate"], page_url, top["top_emotion"]
        )

    # Build evidence
    evidence = []

    if top["avg_rage"] > 0.05:
        evidence.append(EvidenceItem(
            type="rage_clicks",
            value=round(top["avg_rage"] * 100, 1),
            label=f"{round(top['avg_rage'] * 100, 1)}% of clicks show rage patterns",
            session_ids=_get_affected_sessions(db, merchant_id, page_url, "rage"),
        ))

    if top["avg_hesitation"] > 0.1:
        evidence.append(EvidenceItem(
            type="hesitation",
            value=round(top["avg_hesitation"] * 100, 1),
            label=f"{round(top['avg_hesitation'] * 100, 1)}% hesitation score",
        ))

    if top["abandon_rate"] > 0.1:
        evidence.append(EvidenceItem(
            type="drop_off",
            value=round(top["abandon_rate"] * 100, 1),
            label=f"{round(top['abandon_rate'] * 100, 1)}% abandon at this step",
        ))

    if top["avg_scroll_retreat"] > 1:
        evidence.append(EvidenceItem(
            type="session_pattern",
            value=round(top["avg_scroll_retreat"], 1),
            label=f"{round(top['avg_scroll_retreat'], 1)}x scroll retreats (users scroll down then back up)",
        ))

    return DiagnosisResponse(
        summary=summary,
        evidence=evidence,
        root_cause=root_cause,
        actions=actions,
        supporting_charts={
            "page_stats": {
                "total_sessions": top["total_sessions"],
                "avg_friction": round(top["avg_friction"] * 100, 1) if top["avg_friction"] else None,
                "top_emotion": top["top_emotion"],
            }
        },
    )


@router.get(
    "/issues",
    response_model=IssuesListResponse,
    summary="List all detected issues",
)
@limiter.limit("60/minute")
async def list_issues(
    request: Request,
    db: DBSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
    hours: int = Query(default=24, ge=1, le=168, description="Lookback period in hours"),
):
    """Returns a prioritized list of all detected issues.

    Use this for the condensed issue list at the bottom of the
    diagnosis page.

    Uses JWT authentication for merchant identification.
    """

    aggregates = _fetch_page_aggregates(db, merchant.id, hours)

    issues = []
    high_count = 0

    for page in aggregates:
        severity = DiagnosisService._get_severity(
            page["avg_rage"],
            page["avg_hesitation"],
            page["abandon_rate"],
            int(page["avg_scroll_retreat"]),
        )

        if severity == "low" and len(issues) >= 5:
            continue  # Only show top 5 medium/high issues

        if severity == "high":
            high_count += 1

        # Generate title based on dominant signal
        if page["avg_rage"] >= DiagnosisService.RAGE_CLICK_MEDIUM:
            title = "Rage clicking detected on elements"
        elif page["avg_hesitation"] >= DiagnosisService.HESITATION_MEDIUM:
            title = "Users hesitating and uncertain"
        elif page["abandon_rate"] >= DiagnosisService.DROP_OFF_MEDIUM:
            title = "High drop-off rate"
        else:
            title = "Unusual user behavior"

        issues.append(IssueListItem(
            id=f"{hash(page['page_url']) % 10000}",
            title=title,
            page_url=page["page_url"],
            affected_users=page["total_sessions"],
            severity=severity,
        ))

    return IssuesListResponse(
        issues=issues,
        total_issues=len(issues),
        high_severity_count=high_count,
    )
