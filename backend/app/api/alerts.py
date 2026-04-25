"""Alerts API — retention feature for emotion spike notifications."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session as DBSession

from app.core.auth import get_merchant_id as get_merchant_flexible
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.alert import AlertHistory, AlertRule

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


# ── Schemas ─────────────────────────────────────────────────────────


class AlertRuleCreate(BaseModel):
    name: str = Field(..., description="Alert name")
    emotion: str = Field(..., description="Emotion to track: frustration, confusion, anxiety, hesitation")
    threshold: float = Field(..., gt=0, le=100, description="Threshold percentage (0-100)")
    page_url: str | None = Field(None, description="Page URL to monitor, null = any page")
    time_window: str = Field("1h", description="Time window: 1h, 24h, 7d")
    channel: str = Field("email", description="Notification channel: email, webhook")
    webhook_url: str | None = Field(None, description="Webhook URL if channel=webhook")
    cooldown_hours: int = Field(6, ge=1, description="Cooldown period in hours")


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    threshold: float | None = Field(None, gt=0, le=100)
    page_url: str | None = None
    time_window: str | None = None
    channel: str | None = None
    webhook_url: str | None = None
    cooldown_hours: int | None = Field(None, ge=1)
    is_active: bool | None = None


class AlertRuleResponse(BaseModel):
    id: str
    merchant_id: str
    name: str
    emotion: str
    threshold: float
    page_url: str | None
    time_window: str
    channel: str
    webhook_url: str | None
    cooldown_hours: int
    is_active: bool
    last_triggered_at: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AlertHistoryResponse(BaseModel):
    id: str
    alert_rule_id: str
    rule_name: str
    triggered_at: str
    trigger_value: float
    page_url: str
    status: str
    message: str | None

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    rules: list[AlertRuleResponse]
    total: int


# ── Helpers ─────────────────────────────────────────────────────────


def _rule_to_dict(rule: AlertRule) -> dict[str, Any]:
    return {
        "id": str(rule.id),
        "merchant_id": str(rule.merchant_id),
        "name": rule.name,
        "emotion": rule.emotion,
        "threshold": rule.threshold,
        "page_url": rule.page_url,
        "time_window": rule.time_window,
        "channel": rule.channel,
        "webhook_url": rule.webhook_url,
        "cooldown_hours": rule.cooldown_hours,
        "is_active": rule.is_active,
        "last_triggered_at": rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
        "created_at": rule.created_at.isoformat(),
        "updated_at": rule.updated_at.isoformat(),
    }


def _history_to_dict(h: AlertHistory, rule_name: str | None = None) -> dict[str, Any]:
    return {
        "id": str(h.id),
        "alert_rule_id": str(h.alert_rule_id),
        "rule_name": rule_name or "Unknown",
        "triggered_at": h.triggered_at.isoformat(),
        "trigger_value": h.trigger_value,
        "page_url": h.page_url,
        "status": h.status,
        "message": h.message,
    }


# ── Endpoints ───────────────────────────────────────────────────────


@router.post("", response_model=AlertRuleResponse, summary="Create alert rule")
@limiter.limit("30/minute")
async def create_alert_rule(
    request: Request,
    data: AlertRuleCreate,
    db: DBSession = Depends(get_db),
    merchant_id: str = Depends(get_merchant_flexible),
):
    """Create a new alert rule for monitoring emotion spikes."""
    rule = AlertRule(
        merchant_id=uuid.UUID(merchant_id),
        name=data.name,
        emotion=data.emotion,
        threshold=data.threshold,
        page_url=data.page_url,
        time_window=data.time_window,
        channel=data.channel,
        webhook_url=data.webhook_url,
        cooldown_hours=data.cooldown_hours,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return _rule_to_dict(rule)


@router.get("", response_model=AlertListResponse, summary="List alert rules")
@limiter.limit("60/minute")
async def list_alert_rules(
    request: Request,
    db: DBSession = Depends(get_db),
    merchant_id: str = Depends(get_merchant_flexible),
):
    """List all alert rules for the merchant."""
    result = db.execute(
        select(AlertRule)
        .where(AlertRule.merchant_id == uuid.UUID(merchant_id))
        .order_by(AlertRule.created_at.desc())
    )
    rules = result.scalars().all()
    return {
        "rules": [_rule_to_dict(r) for r in rules],
        "total": len(rules),
    }


@router.get("/{rule_id}", response_model=AlertRuleResponse, summary="Get alert rule")
@limiter.limit("60/minute")
async def get_alert_rule(
    request: Request,
    rule_id: str,
    db: DBSession = Depends(get_db),
    merchant_id: str = Depends(get_merchant_flexible),
):
    """Get a single alert rule by ID."""
    try:
        rule_uid = uuid.UUID(rule_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID")

    result = db.execute(
        select(AlertRule).where(
            and_(
                AlertRule.id == rule_uid,
                AlertRule.merchant_id == uuid.UUID(merchant_id),
            )
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return _rule_to_dict(rule)


@router.put("/{rule_id}", response_model=AlertRuleResponse, summary="Update alert rule")
@limiter.limit("30/minute")
async def update_alert_rule(
    request: Request,
    rule_id: str,
    data: AlertRuleUpdate,
    db: DBSession = Depends(get_db),
    merchant_id: str = Depends(get_merchant_flexible),
):
    """Update an existing alert rule."""
    try:
        rule_uid = uuid.UUID(rule_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID")

    result = db.execute(
        select(AlertRule).where(
            and_(
                AlertRule.id == rule_uid,
                AlertRule.merchant_id == uuid.UUID(merchant_id),
            )
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    # Update fields
    if data.name is not None:
        rule.name = data.name
    if data.threshold is not None:
        rule.threshold = data.threshold
    if data.page_url is not None:
        rule.page_url = data.page_url
    if data.time_window is not None:
        rule.time_window = data.time_window
    if data.channel is not None:
        rule.channel = data.channel
    if data.webhook_url is not None:
        rule.webhook_url = data.webhook_url
    if data.cooldown_hours is not None:
        rule.cooldown_hours = data.cooldown_hours
    if data.is_active is not None:
        rule.is_active = data.is_active

    rule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rule)
    return _rule_to_dict(rule)


@router.delete("/{rule_id}", summary="Delete alert rule")
@limiter.limit("30/minute")
async def delete_alert_rule(
    request: Request,
    rule_id: str,
    db: DBSession = Depends(get_db),
    merchant_id: str = Depends(get_merchant_flexible),
):
    """Delete an alert rule."""
    try:
        rule_uid = uuid.UUID(rule_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID")

    result = db.execute(
        select(AlertRule).where(
            and_(
                AlertRule.id == rule_uid,
                AlertRule.merchant_id == uuid.UUID(merchant_id),
            )
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    db.delete(rule)
    db.commit()
    return {"status": "deleted"}


@router.get("/history/list", response_model=list[AlertHistoryResponse], summary="Get alert history")
@limiter.limit("60/minute")
async def get_alert_history(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    db: DBSession = Depends(get_db),
    merchant_id: str = Depends(get_merchant_flexible),
):
    """Get alert trigger history for the merchant."""
    # Join with AlertRule to get rule names
    result = db.execute(
        select(AlertHistory, AlertRule.name)
        .join(AlertRule, AlertHistory.alert_rule_id == AlertRule.id)
        .where(AlertRule.merchant_id == uuid.UUID(merchant_id))
        .order_by(AlertHistory.triggered_at.desc())
        .limit(limit)
    )
    rows = result.all()
    return [_history_to_dict(h, rule_name) for h, rule_name in rows]


@router.get("/unresolved-count", summary="Get unresolved alert count")
@limiter.limit("60/minute")
async def get_unresolved_count(
    request: Request,
    db: DBSession = Depends(get_db),
    merchant_id: str = Depends(get_merchant_flexible),
):
    """Count of unresolved alerts from last 24 hours (for sidebar badge)."""
    cutoff = datetime.utcnow() - timedelta(hours=24)

    rule_ids_result = db.execute(
        select(AlertRule.id).where(AlertRule.merchant_id == uuid.UUID(merchant_id))
    )
    rule_ids = [r[0] for r in rule_ids_result.all()]

    if not rule_ids:
        return {"count": 0}

    result = db.execute(
        select(func.count(AlertHistory.id))
        .where(
            and_(
                AlertHistory.alert_rule_id.in_(rule_ids),
                AlertHistory.status == "fired",
                AlertHistory.triggered_at >= cutoff,
            )
        )
    )
    count = result.scalar() or 0
    return {"count": count}


@router.post("/check", summary="Manually trigger alert check")
@limiter.limit("10/minute")
async def check_alerts(
    request: Request,
    db: DBSession = Depends(get_db),
    merchant_id: str = Depends(get_merchant_flexible),
):
    """Check alert rules and fire if thresholds met (for testing)."""
    from app.services.alert_checker import check_alerts

    fired = check_alerts(db)

    return {
        "status": "checked",
        "fired": fired,
        "message": f"Checked {merchant_id}'s alert rules - {fired} fired",
    }
