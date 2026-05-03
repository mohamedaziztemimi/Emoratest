"""Diagnosis Engine — detects actionable issues from behavioral signals.

This is EmoraTest's core value prop: turning raw behavior into
specific, actionable fixes. Each issue type has:
- Clear detection rule (threshold-based)
- Severity classification
- Human-readable title/description
- Specific recommendation

ALL detection rules are based on behavioral signals only —
no ML emotion predictions required. This makes diagnosis reliable
and immediately valuable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import func, and_, cast, Integer
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.session import Session
from app.models.session_features import SessionFeatures


@dataclass
class Issue:
    """A detected problem on a page."""

    type: str
    severity: str  # "critical" | "warning" | "info"
    title: str
    description: str
    affected_sessions: int
    affected_percentage: float
    recommendation: str


@dataclass
class PageIssues:
    """All issues detected for a single page."""

    page_url: str
    page_name: str
    total_sessions: int
    issues: list[Issue]

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "critical")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "info")


class DiagnosisEngine:
    """Detects issues from behavioral signals.

    Thresholds are based on analysis of real user behavior and
    can be tuned as we gather more data.
    """

    # Rage click thresholds
    RAGE_CLICK_CRITICAL = 0.3  # 30% of sessions show rage clicks
    RAGE_CLICK_WARNING = 0.15  # 15% of sessions show rage clicks

    # Bounce/short session thresholds
    BOUNCE_CRITICAL_THRESHOLD = 0.5  # 50% bounce rate
    BOUNCE_WARNING_THRESHOLD = 0.3  # 30% bounce rate
    SHORT_SESSION_SECONDS = 10  # Sessions under 10 seconds

    # Scroll confusion thresholds
    SCROLL_CONFUSION_RETREATS = 3  # Average 3+ retreats per session

    # Form abandonment thresholds
    FORM_ABANDON_CRITICAL = 0.3  # 30% abandonment rate
    FORM_ABANDON_WARNING = 0.2  # 20% abandonment rate

    # Hesitation thresholds
    HESITATION_CRITICAL = 0.5  # Average hesitation score
    HESITATION_WARNING = 0.35

    # Engagement thresholds
    LOW_ENGAGEMENT_RATIO = 0.3  # Less than 30% active engagement

    # Minimum sessions for reliable diagnosis
    MIN_SESSIONS_PER_PAGE = 5

    @staticmethod
    def _extract_page_name(url: str) -> str:
        """Extract human-readable page name from URL."""
        try:
            path = urlparse(url).path
            parts = [p for p in path.split("/") if p and not p.isdigit()]
            if parts:
                return " ".join(
                    p.replace("-", " ").replace("_", " ").title() for p in parts[-2:]
                )
            return "Homepage"
        except Exception:
            return "Page"

    @staticmethod
    def _detect_rage_clicks(
        page_url: str,
        total_sessions: int,
        rage_sessions: int,
    ) -> Issue | None:
        """Detect rage click clusters.

        Rule: If >= 20% of sessions have rage_click_score > 0.3
        """
        if total_sessions < DiagnosisEngine.MIN_SESSIONS_PER_PAGE:
            return None

        rage_percentage = (rage_sessions / total_sessions * 100) if total_sessions else 0

        if rage_percentage < 15:  # Below warning threshold
            return None

        severity = "critical" if rage_percentage >= 30 else "warning"

        return Issue(
            type="rage_click_cluster",
            severity=severity,
            title=f"Rage clicks detected on {DiagnosisEngine._extract_page_name(page_url)}",
            description=(
                f"{rage_percentage:.1f}% of sessions ({rage_sessions} sessions) show rage clicking behavior. "
                "Users are clicking repeatedly on elements that don't respond as expected."
            ),
            affected_sessions=rage_sessions,
            affected_percentage=round(rage_percentage, 1),
            recommendation=(
                "Check for broken buttons, slow-loading elements, or misleading "
                "clickable-looking elements on this page. Test all interactive elements."
            ),
        )

    @staticmethod
    def _detect_high_bounce(
        page_url: str,
        total_sessions: int,
        short_sessions: int,
    ) -> Issue | None:
        """Detect high bounce rate / short sessions.

        Rule: If >= 30% of sessions are under 10 seconds
        Severity: critical if >= 50%, warning if >= 30%
        """
        if total_sessions < DiagnosisEngine.MIN_SESSIONS_PER_PAGE:
            return None

        bounce_percentage = (short_sessions / total_sessions * 100) if total_sessions else 0

        if bounce_percentage < 25:  # Below meaningful threshold
            return None

        severity = "critical" if bounce_percentage >= 50 else "warning"

        return Issue(
            type="high_bounce",
            severity=severity,
            title=f"High bounce rate on {DiagnosisEngine._extract_page_name(page_url)}",
            description=(
                f"{bounce_percentage:.1f}% of visitors leave within 10 seconds. "
                f"({short_sessions} of {total_sessions} sessions)"
            ),
            affected_sessions=short_sessions,
            affected_percentage=round(bounce_percentage, 1),
            recommendation=(
                "Review page load speed, above-the-fold content, and whether the page "
                "matches user expectations from the referring link. Consider adding "
                "engaging content or a clear value proposition."
            ),
        )

    @staticmethod
    def _detect_scroll_confusion(
        page_url: str,
        avg_scroll_retreats: float | None,
        total_sessions: int,
    ) -> Issue | None:
        """Detect scroll confusion.

        Rule: If average scroll_retreat_count > 3 for a page
        """
        if total_sessions < DiagnosisEngine.MIN_SESSIONS_PER_PAGE:
            return None

        if avg_scroll_retreats is None or avg_scroll_retreats <= 3:
            return None

        return Issue(
            type="scroll_confusion",
            severity="warning",
            title=f"Users scroll back and forth on {DiagnosisEngine._extract_page_name(page_url)}",
            description=(
                f"Users reverse scroll direction an average of {avg_scroll_retreats:.1f} times "
                "per session, suggesting they can't find what they're looking for."
            ),
            affected_sessions=total_sessions,  # Affects all sessions on this page
            affected_percentage=100.0,
            recommendation=(
                "Review content structure and navigation. Consider adding anchor links, "
                "a table of contents, or reorganizing content to follow a logical flow."
            ),
        )

    @staticmethod
    def _detect_form_abandonment(
        page_url: str,
        total_sessions: int,
        abandon_sessions: int,
        form_interaction_sessions: int,
    ) -> Issue | None:
        """Detect form abandonment.

        CRITICAL: Only trigger if users actually interacted with form elements.
        We check for events with element_type in ('form', 'input', 'textarea', 'select').
        Users leaving a page without form interaction is normal browsing, NOT form abandonment.

        Rule: If >= 25% of sessions with form interactions have exit_intent_count > 0
        """
        if total_sessions < DiagnosisEngine.MIN_SESSIONS_PER_PAGE:
            return None

        # If no one interacted with forms, this is NOT form abandonment
        if form_interaction_sessions == 0:
            return None

        # Calculate abandonment rate ONLY among sessions that had form interactions
        form_abandon_percentage = (abandon_sessions / form_interaction_sessions * 100) if form_interaction_sessions else 0

        if form_abandon_percentage < 20:  # Below warning threshold
            return None

        severity = "critical" if form_abandon_percentage >= 35 else "warning"

        return Issue(
            type="form_abandonment",
            severity=severity,
            title=f"Form abandonment detected on {DiagnosisEngine._extract_page_name(page_url)}",
            description=(
                f"{form_abandon_percentage:.1f}% of users who interacted with forms exited unexpectedly. "
                f"({abandon_sessions} of {form_interaction_sessions} form sessions)"
            ),
            affected_sessions=abandon_sessions,
            affected_percentage=round(form_abandon_percentage, 1),
            recommendation=(
                "Simplify the form, reduce required fields, add progress indicators, "
                "or break into multiple steps. Consider saving progress so users can return later."
            ),
        )

    @staticmethod
    def _detect_hesitation(
        page_url: str,
        avg_hesitation: float | None,
        total_sessions: int,
        affected_sessions: int,
    ) -> Issue | None:
        """Detect hesitation before action.

        Rule: If average hesitation_score > 0.4
        """
        if total_sessions < DiagnosisEngine.MIN_SESSIONS_PER_PAGE:
            return None

        if avg_hesitation is None or avg_hesitation <= 0.35:
            return None

        severity = "critical" if avg_hesitation >= 0.5 else "warning"
        hesitation_pct = round(avg_hesitation * 100, 1)

        return Issue(
            type="hesitation",
            severity=severity,
            title=f"Users hesitate before taking action on {DiagnosisEngine._extract_page_name(page_url)}",
            description=(
                f"Users pause for extended periods before clicking. "
                f"Average hesitation score: {hesitation_pct}%."
            ),
            affected_sessions=affected_sessions,
            affected_percentage=hesitation_pct,
            recommendation=(
                "Clarify your call-to-action. Make pricing, terms, or next steps more transparent. "
                "Consider adding trust signals (reviews, guarantees) near decision points."
            ),
        )

    @staticmethod
    def _detect_low_engagement(
        page_url: str,
        total_sessions: int,
        avg_engagement_ratio: float | None,
    ) -> Issue | None:
        """Detect low engagement.

        Rule: If average dwell_active_engagement_ratio < 0.3
        Note: We use velocity_variance as a proxy — low variance = low engagement
        """
        if total_sessions < DiagnosisEngine.MIN_SESSIONS_PER_PAGE:
            return None

        # For now, skip this detection as we don't have a direct engagement metric
        # This can be added later when we track dwell time vs active interaction
        return None

    @classmethod
    def analyze_page(
        cls,
        db: Session,
        merchant_id: str,
        page_url: str,
        since: datetime,
    ) -> PageIssues | None:
        """Analyze a single page for all issue types."""
        # Get session count for this page
        total_sessions = db.query(func.count(Session.id)).filter(
            and_(
                Session.merchant_id == merchant_id,
                Session.page_url == page_url,
                Session.started_at >= since,
            )
        ).scalar() or 0

        if total_sessions < cls.MIN_SESSIONS_PER_PAGE:
            return None

        issues: list[Issue] = []

        # Get feature aggregates for this page
        features_agg = (
            db.query(
                func.avg(SessionFeatures.rage_click_score).label("avg_rage"),
                func.avg(SessionFeatures.hesitation_score).label("avg_hesitation"),
                func.avg(SessionFeatures.scroll_retreat_count).label("avg_scroll_retreat"),
                func.avg(SessionFeatures.exit_intent_count).label("avg_exit_intent"),
                func.avg(SessionFeatures.session_duration_s).label("avg_duration"),
            )
            .join(Session, SessionFeatures.session_id == Session.id)
            .filter(
                and_(
                    Session.merchant_id == merchant_id,
                    Session.page_url == page_url,
                    Session.started_at >= since,
                )
            )
            .first()
        )

        if not features_agg:
            return None

        # Count sessions with rage clicks (> 0.3 threshold)
        rage_sessions = (
            db.query(func.count(Session.id))
            .join(SessionFeatures, SessionFeatures.session_id == Session.id)
            .filter(
                and_(
                    Session.merchant_id == merchant_id,
                    Session.page_url == page_url,
                    Session.started_at >= since,
                    SessionFeatures.rage_click_score > 0.3,
                )
            )
            .scalar() or 0
        )

        # Count short sessions (< 10 seconds)
        short_sessions = (
            db.query(func.count(Session.id))
            .filter(
                and_(
                    Session.merchant_id == merchant_id,
                    Session.page_url == page_url,
                    Session.started_at >= since,
                    Session.ended_at.isnot(None),
                    func.extract(
                        "epoch", Session.ended_at - Session.started_at
                    ) < cls.SHORT_SESSION_SECONDS,
                )
            )
            .scalar() or 0
        )

        # Count sessions with form interactions (form, input, textarea, select)
        # Subquery to find sessions that have at least one form-related event
        form_interaction_subquery = (
            db.query(Event.session_id)
            .filter(
                and_(
                    Event.element_type.in_(["form", "input", "textarea", "select"]),
                )
            )
            .distinct()
            .subquery()
        )

        form_interaction_sessions = (
            db.query(func.count(Session.id))
            .join(
                form_interaction_subquery,
                Session.id == form_interaction_subquery.c.session_id
            )
            .filter(
                and_(
                    Session.merchant_id == merchant_id,
                    Session.page_url == page_url,
                    Session.started_at >= since,
                )
            )
            .scalar() or 0
        )

        # Count sessions with BOTH form interactions AND exit intent (actual form abandonment)
        exit_intent_with_form_subquery = (
            db.query(Event.session_id)
            .filter(
                and_(
                    Event.element_type.in_(["form", "input", "textarea", "select"]),
                )
            )
            .distinct()
            .subquery()
        )

        exit_sessions = (
            db.query(func.count(Session.id))
            .join(SessionFeatures, SessionFeatures.session_id == Session.id)
            .join(
                exit_intent_with_form_subquery,
                Session.id == exit_intent_with_form_subquery.c.session_id
            )
            .filter(
                and_(
                    Session.merchant_id == merchant_id,
                    Session.page_url == page_url,
                    Session.started_at >= since,
                    SessionFeatures.exit_intent_count > 0,
                )
            )
            .scalar() or 0
        )

        # Count sessions with hesitation (> 0.3 threshold)
        hesitation_sessions = (
            db.query(func.count(Session.id))
            .join(SessionFeatures, SessionFeatures.session_id == Session.id)
            .filter(
                and_(
                    Session.merchant_id == merchant_id,
                    Session.page_url == page_url,
                    Session.started_at >= since,
                    SessionFeatures.hesitation_score > 0.3,
                )
            )
            .scalar() or 0
        )

        # Run all detectors
        rage_issue = cls._detect_rage_clicks(
            page_url, total_sessions, rage_sessions
        )
        if rage_issue:
            issues.append(rage_issue)

        bounce_issue = cls._detect_high_bounce(
            page_url, total_sessions, short_sessions
        )
        if bounce_issue:
            issues.append(bounce_issue)

        scroll_issue = cls._detect_scroll_confusion(
            page_url, features_agg.avg_scroll_retreat, total_sessions
        )
        if scroll_issue:
            issues.append(scroll_issue)

        form_issue = cls._detect_form_abandonment(
            page_url, total_sessions, exit_sessions, form_interaction_sessions
        )
        if form_issue:
            issues.append(form_issue)

        hesitation_issue = cls._detect_hesitation(
            page_url, features_agg.avg_hesitation, total_sessions, hesitation_sessions
        )
        if hesitation_issue:
            issues.append(hesitation_issue)

        low_engagement_issue = cls._detect_low_engagement(
            page_url, total_sessions, features_agg.avg_rage  # proxy for now
        )
        if low_engagement_issue:
            issues.append(low_engagement_issue)

        if not issues:
            return None

        return PageIssues(
            page_url=page_url,
            page_name=cls._extract_page_name(page_url),
            total_sessions=total_sessions,
            issues=issues,
        )

    @classmethod
    def diagnose_all_pages(
        cls,
        db: Session,
        merchant_id: str,
        days: int = 7,
        limit: int = 20,
    ) -> list[PageIssues]:
        """Analyze all pages and return detected issues.

        Returns pages sorted by severity (critical first).
        """
        since = datetime.utcnow() - timedelta(days=days)

        # Get all pages with sessions in the time window
        pages = (
            db.query(Session.page_url)
            .filter(
                and_(
                    Session.merchant_id == merchant_id,
                    Session.started_at >= since,
                )
            )
            .group_by(Session.page_url)
            .all()
        )

        all_issues: list[PageIssues] = []

        for (page_url,) in pages:
            page_issues = cls.analyze_page(db, merchant_id, page_url, since)
            if page_issues:
                all_issues.append(page_issues)

        # Sort by severity: critical first, then warnings, then info
        # Within each severity, sort by affected percentage
        def severity_score(page: PageIssues) -> tuple[int, int, float]:
            return (
                -page.critical_count,
                -page.warning_count,
                -max((i.affected_percentage for i in page.issues), default=0),
            )

        all_issues.sort(key=severity_score)

        return all_issues[:limit]
