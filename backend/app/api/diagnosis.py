"""Diagnosis API — turns behavior signals into actionable fixes.

Returns pages with detected issues, sorted by severity.
Each issue includes:
- Type (rage_click_cluster, high_bounce, scroll_confusion, etc.)
- Severity (critical | warning | info)
- Title and description with specific numbers
- Recommendation for fixing
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.auth import get_current_merchant
from app.models.merchant import Merchant
from app.services.diagnosis import DiagnosisEngine, PageIssues, Issue
from sqlalchemy.orm import Session as DBSession

router = APIRouter(prefix="/api/v1/diagnosis", tags=["diagnosis"])


# ─────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────


class IssueItem(BaseModel):
    """A detected issue on a page."""

    type: str = Field(..., description="Issue type identifier")
    severity: str = Field(..., description="critical | warning | info")
    title: str = Field(..., description="Human-readable issue title")
    description: str = Field(..., description="Detailed explanation with numbers")
    affected_sessions: int = Field(..., description="Count of affected sessions")
    affected_percentage: float = Field(..., description="% of sessions affected")
    recommendation: str = Field(..., description="Specific action to take")


class PageIssueItem(BaseModel):
    """A page with its detected issues."""

    page_url: str = Field(..., description="Page URL")
    page_name: str = Field(..., description="Human-readable page name")
    total_sessions: int = Field(..., description="Total sessions on this page")
    issue_count: int = Field(..., description="Total issues detected")
    critical_count: int = Field(..., description="Critical issues")
    issues: list[IssueItem] = Field(default_factory=list, description="List of issues")


class DiagnosisResponse(BaseModel):
    """Complete diagnosis response."""

    pages: list[PageIssueItem] = Field(default_factory=list, description="Pages with issues")
    total_pages: int = Field(..., description="Total pages analyzed")
    critical_issues: int = Field(..., description="Total critical issues across all pages")
    warning_issues: int = Field(..., description="Total warning issues")
    info_issues: int = Field(..., description="Total info issues")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────


def _issue_to_schema(issue: Issue) -> IssueItem:
    """Convert internal Issue to API schema."""
    return IssueItem(
        type=issue.type,
        severity=issue.severity,
        title=issue.title,
        description=issue.description,
        affected_sessions=issue.affected_sessions,
        affected_percentage=issue.affected_percentage,
        recommendation=issue.recommendation,
    )


def _page_to_schema(page: PageIssues) -> PageIssueItem:
    """Convert internal PageIssues to API schema."""
    return PageIssueItem(
        page_url=page.page_url,
        page_name=page.page_name,
        total_sessions=page.total_sessions,
        issue_count=len(page.issues),
        critical_count=page.critical_count,
        issues=[_issue_to_schema(i) for i in page.issues],
    )


# ─────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=DiagnosisResponse,
    summary="Get diagnosis for all pages",
)
@limiter.limit("60/minute")
async def get_diagnosis(
    request: Request,
    db: DBSession = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
    days: int = Query(default=7, ge=1, le=90, description="Lookback period in days"),
    limit: int = Query(default=20, ge=1, le=100, description="Max pages to return"),
):
    """Returns all pages with detected issues, sorted by severity.

    Each page shows its list of issues with:
    - Issue type and severity badge
    - Title and description with specific numbers
    - Recommendation for fixing

    Uses JWT authentication for merchant identification.
    """
    page_issues_list = DiagnosisEngine.diagnose_all_pages(
        db, merchant.id, days=days, limit=limit
    )

    # Count total issues by severity
    total_critical = sum(p.critical_count for p in page_issues_list)
    total_warning = sum(p.warning_count for p in page_issues_list)
    total_info = sum(p.info_count for p in page_issues_list)

    return DiagnosisResponse(
        pages=[_page_to_schema(p) for p in page_issues_list],
        total_pages=len(page_issues_list),
        critical_issues=total_critical,
        warning_issues=total_warning,
        info_issues=total_info,
    )
