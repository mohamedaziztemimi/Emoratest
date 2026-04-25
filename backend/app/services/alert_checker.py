"""Alert checker service — runs on schedule to evaluate alert rules.

In production, set up a cron job to call this every 5 minutes:

    */5 * * * * curl -X POST http://localhost:8000/api/v1/alerts/check

Or use a background task scheduler like APScheduler or Celery Beat.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.orm import Session as DBSession

from app.models.alert import AlertHistory, AlertRule
from app.models.session import Session


def check_alerts(db: DBSession) -> int:
    """Check all active alert rules and fire if thresholds are met.

    Returns:
        Number of alerts fired.
    """
    # Get all active alert rules
    result = db.execute(
        select(AlertRule).where(AlertRule.is_active == True)
    )
    rules = result.scalars().all()

    fired_count = 0

    for rule in rules:
        # Check cooldown
        if rule.last_triggered_at:
            cooldown_end = rule.last_triggered_at + timedelta(hours=rule.cooldown_hours)
            if datetime.utcnow() < cooldown_end:
                # Still in cooldown period
                continue

        # Determine time window cutoff
        if rule.time_window == "1h":
            cutoff = datetime.utcnow() - timedelta(hours=1)
        elif rule.time_window == "24h":
            cutoff = datetime.utcnow() - timedelta(days=1)
        elif rule.time_window == "7d":
            cutoff = datetime.utcnow() - timedelta(days=7)
        else:
            cutoff = datetime.utcnow() - timedelta(hours=1)  # Default to 1h

        # Build base query for sessions in time window
        base_query = (
            select(Session)
            .where(Session.merchant_id == rule.merchant_id)
            .where(Session.created_at >= cutoff)
        )

        # Filter by page if specified
        if rule.page_url:
            base_query = base_query.where(Session.page_url == rule.page_url)

        # Count total sessions in window
        total_result = db.execute(
            select(func.count(Session.id)).where(
                and_(
                    Session.merchant_id == rule.merchant_id,
                    Session.created_at >= cutoff,
                    Session.page_url == rule.page_url if rule.page_url else True,
                )
            )
        )
        total_sessions = total_result.scalar() or 0

        if total_sessions == 0:
            continue  # No sessions to evaluate

        # Count sessions with the target emotion
        emotion_result = db.execute(
            select(func.count(Session.id)).where(
                and_(
                    Session.merchant_id == rule.merchant_id,
                    Session.created_at >= cutoff,
                    Session.primary_emotion == rule.emotion,
                    Session.page_url == rule.page_url if rule.page_url else True,
                )
            )
        )
        emotion_sessions = emotion_result.scalar() or 0

        # Calculate percentage
        emotion_pct = (emotion_sessions / total_sessions) * 100

        # Fire alert if threshold is met
        if emotion_pct >= rule.threshold:
            # Create alert history record
            history = AlertHistory(
                alert_rule_id=rule.id,
                trigger_value=round(emotion_pct, 2),
                page_url=rule.page_url or "all pages",
                message=f"{rule.emotion.capitalize()} reached {emotion_pct:.1f}% on {rule.page_url or 'all pages'} (threshold: {rule.threshold}%)",
            )
            db.add(history)

            # Update rule's last triggered time
            rule.last_triggered_at = datetime.utcnow()

            fired_count += 1

            # Here you would send the actual notification
            # For email: use SendGrid/AWS SES
            # For webhook: make HTTP POST to rule.webhook_url
            _send_notification(rule, emotion_pct)

    db.commit()
    return fired_count


def _send_notification(rule: AlertRule, trigger_value: float) -> None:
    """Send notification for fired alert.

    Args:
        rule: The alert rule that fired
        trigger_value: The actual emotion percentage that triggered it

    Note:
        This is a placeholder. Implement actual notification logic:
        - Email: Use SendGrid, AWS SES, or similar
        - Webhook: Make HTTP POST with alert details
    """
    # TODO: Implement actual notification sending
    # Example webhook:
    # if rule.channel == "webhook" and rule.webhook_url:
    #     httpx.post(
    #         rule.webhook_url,
    #         json={
    #             "rule_id": str(rule.id),
    #             "rule_name": rule.name,
    #             "emotion": rule.emotion,
    #             "trigger_value": trigger_value,
    #             "threshold": rule.threshold,
    #             "page_url": rule.page_url,
    #             "timestamp": datetime.utcnow().isoformat(),
    #         },
    #         timeout=10,
    #     )
    pass
