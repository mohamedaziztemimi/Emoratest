"""Alert checker service — runs on schedule to evaluate alert rules.

In production, set up a cron job to call this every 5 minutes:

    */5 * * * * curl -X POST http://localhost:8000/api/v1/alerts/check

Or use a background task scheduler like APScheduler or Celery Beat.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta

import httpx
from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.orm import Session as DBSession

from app.models.alert import AlertHistory, AlertRule
from app.models.merchant import Merchant
from app.models.session import Session

logger = logging.getLogger(__name__)


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

            # Send notification
            _send_notification(rule, emotion_pct, db)

    db.commit()
    return fired_count


def _send_notification(rule: AlertRule, trigger_value: float, db: DBSession) -> None:
    """Send notification for fired alert.

    Args:
        rule: The alert rule that fired
        trigger_value: The actual emotion percentage that triggered it
        db: Database session for fetching merchant info
    """
    try:
        # Get merchant email for notification
        merchant = db.execute(
            select(Merchant).where(Merchant.id == rule.merchant_id)
        ).scalar_one_or_none()

        if not merchant:
            logger.warning(f"Merchant {rule.merchant_id} not found for alert {rule.id}")
            return

        # Build alert payload
        alert_payload = {
            "rule_id": str(rule.id),
            "rule_name": rule.name,
            "emotion": rule.emotion,
            "trigger_value": trigger_value,
            "threshold": rule.threshold,
            "page_url": rule.page_url or "all pages",
            "time_window": rule.time_window,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Send based on channel
        if rule.channel == "email":
            _send_email_notification(rule, trigger_value, merchant.email, db)
        elif rule.channel == "webhook" and rule.webhook_url:
            _send_webhook_notification(rule.webhook_url, alert_payload)

        logger.info(f"Notification sent for alert {rule.name} via {rule.channel}")
    except Exception as e:
        logger.error(f"Failed to send notification for alert {rule.id}: {e}")


def _send_email_notification(
    rule: AlertRule,
    trigger_value: float,
    merchant_email: str,
    db: DBSession,
) -> None:
    """Send email notification for fired alert.

    Uses asyncio.run() to call the async EmailService from sync code.
    """
    from app.services.email import email_service

    async def send_email():
        return await email_service.send_alert_notification(
            to=merchant_email,
            alert_name=rule.name,
            emotion=rule.emotion,
            trigger_value=trigger_value,
            threshold=rule.threshold,
            page_url=rule.page_url or "all pages",
            time_window=rule.time_window,
        )

    try:
        # Run the async email function in the current event loop
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(send_email())
        if success:
            logger.info(f"Alert email sent to {merchant_email} for {rule.name}")
        else:
            logger.warning(f"Failed to send alert email to {merchant_email}")
    except RuntimeError:
        # No event loop running, create a new one
        success = asyncio.run(send_email())
        if success:
            logger.info(f"Alert email sent to {merchant_email} for {rule.name}")
        else:
            logger.warning(f"Failed to send alert email to {merchant_email}")
    except Exception as e:
        logger.error(f"Error sending alert email: {e}")


def _send_webhook_notification(webhook_url: str, payload: dict) -> None:
    """Send webhook notification for fired alert.

    Supports both generic webhooks and Slack webhooks.
    """
    try:
        # Check if this is a Slack webhook
        if "hooks.slack.com" in webhook_url:
            _send_slack_webhook(webhook_url, payload)
        else:
            _send_generic_webhook(webhook_url, payload)
    except Exception as e:
        logger.error(f"Failed to send webhook to {webhook_url}: {e}")


def _send_slack_webhook(webhook_url: str, payload: dict) -> None:
    """Send formatted Slack webhook notification."""
    # Behavioral state emoji mapping
    emotion_emojis = {
        "frustrated": "😤",
        "confused": "😕",
        "hesitating": "🤔",
        "engaged": "😊",
        "disengaged": "😴",
    }
    emoji = emotion_emojis.get(payload.get("emotion", ""), "⚠️")

    # Color based on behavioral state severity
    emotion_colors = {
        "frustrated": "danger",
        "confused": "warning",
        "hesitating": "warning",
        "engaged": "good",
        "disengaged": "#6B7280",
    }
    color = emotion_colors.get(payload.get("emotion", ""), "warning")

    # Convert color name to hex for Slack
    color_hex = {
        "danger": "#EF4444",
        "warning": "#F59E0B",
        "good": "#10B981",
    }.get(color, "#007BFF")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} Alert Fired: {payload.get('rule_name', 'Unknown')}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Emotion:*\n{payload.get('emotion', 'Unknown').capitalize()} {emoji}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Current Value:*\n{payload.get('trigger_value', 0):.1f}%",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Threshold:*\n{payload.get('threshold', 0):.0f}%",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Time Window:*\n{payload.get('time_window', '1h')}",
                },
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Page:*\n{payload.get('page_url', 'all pages')}",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Dashboard",
                        "emoji": True,
                    },
                    "url": "https://emoratest.com/dashboard/sessions",
                    "style": "primary",
                }
            ],
        },
    ]

    slack_payload = {"blocks": blocks}

    response = httpx.post(
        webhook_url,
        json=slack_payload,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    response.raise_for_status()
    logger.info(f"Slack webhook sent successfully to {webhook_url}")


def _send_generic_webhook(webhook_url: str, payload: dict) -> None:
    """Send generic webhook notification."""
    response = httpx.post(
        webhook_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    response.raise_for_status()
    logger.info(f"Generic webhook sent successfully to {webhook_url}")
