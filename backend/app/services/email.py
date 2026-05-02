"""Email service for sending transactional emails.

Supports multiple providers:
- console: Print to stdout (development)
- resend: Resend.com API
- sendgrid: SendGrid API
- smtp: Generic SMTP server
"""

import logging
from datetime import UTC, datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import Literal

import httpx

from app.core.config import settings

EmailProvider = Literal["console", "resend", "sendgrid", "smtp"]

logger = logging.getLogger(__name__)


class EmailService:
    """Email service with multiple provider support."""

    def __init__(self) -> None:
        self.provider: EmailProvider = settings.EMAIL_PROVIDER
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """Send an email using the configured provider.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        try:
            if self.provider == "console":
                return self._send_console(to, subject, html_content, text_content)
            elif self.provider == "resend":
                return await self._send_resend(to, subject, html_content)
            elif self.provider == "sendgrid":
                return await self._send_sendgrid(to, subject, html_content)
            elif self.provider == "smtp":
                return await self._send_smtp(to, subject, html_content, text_content)
            else:
                logger.warning(f"Unknown email provider: {self.provider}, falling back to console")
                return self._send_console(to, subject, html_content, text_content)
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False

    def _send_console(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """Print email to console (development mode)."""
        print("\n" + "=" * 60)
        print(f"EMAIL TO: {to}")
        print(f"SUBJECT: {subject}")
        print(f"FROM: {self.from_name} <{self.from_email}>")
        print("-" * 60)
        print(f"HTML:\n{html_content}")
        if text_content:
            print(f"\nTEXT:\n{text_content}")
        print("=" * 60 + "\n")
        return True

    async def _send_resend(
        self,
        to: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """Send email using Resend.com API."""
        if not settings.RESEND_API_KEY:
            logger.error("RESEND_API_KEY not configured")
            return False

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"{self.from_name} <{self.from_email}>",
                    "to": [to],
                    "subject": subject,
                    "html": html_content,
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                logger.info(f"Email sent via Resend to {to}")
                return True
            else:
                logger.error(f"Resend API error: {response.text}")
                return False

    async def _send_sendgrid(
        self,
        to: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """Send email using SendGrid API."""
        if not settings.SENDGRID_API_KEY:
            logger.error("SENDGRID_API_KEY not configured")
            return False

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [
                        {
                            "to": [{"email": to}],
                            "subject": subject,
                        }
                    ],
                    "from": {"email": self.from_email, "name": self.from_name},
                    "content": [{"type": "text/html", "value": html_content}],
                },
                timeout=10.0,
            )

            if response.status_code in (200, 202):
                logger.info(f"Email sent via SendGrid to {to}")
                return True
            else:
                logger.error(f"SendGrid API error: {response.text}")
                return False

    async def _send_smtp(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """Send email using SMTP."""
        if not settings.SMTP_HOST:
            logger.error("SMTP_HOST not configured")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to
            msg["Subject"] = subject

            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email sent via SMTP to {to}")
            return True
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False

    async def send_password_reset(
        self,
        to: str,
        reset_link: str,
        expiry_minutes: int = 30,
    ) -> bool:
        """Send password reset email."""
        subject = "Reset Your EmoraTest Password"
        expiry_time = (datetime.now(UTC) + timedelta(minutes=expiry_minutes)).strftime("%I:%M %p")

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f6fa;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f6fa; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #007BFF;">EmoraTest</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 600; color: #111318;">Reset Your Password</h2>
                            <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #6B7280;">
                                We received a request to reset your password. Click the button below to create a new password.
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{reset_link}" style="display: inline-block; background: #007BFF; color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-size: 15px; font-weight: 600;">
                                            Reset Password
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 24px 0 8px 0; font-size: 14px; color: #6B7280;">
                                Or copy and paste this link:
                            </p>
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #007BFF; word-break: break-all;">
                                <a href="{reset_link}" style="color: #007BFF; word-break: break-all;">{reset_link}</a>
                            </p>
                            <p style="margin: 16px 0 8px 0; font-size: 14px; color: #6B7280;">
                                This link will expire in {expiry_minutes} minutes.
                            </p>
                            <p style="margin: 0; font-size: 14px; color: #6B7280;">
                                If you didn't request this password reset, you can safely ignore this email.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; text-align: center;">
                            <p style="margin: 0; font-size: 13px; color: #9CA3AF;">
                                &copy; 2026 EmoraTest. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        text_content = f"""
Reset Your EmoraTest Password

We received a request to reset your password. Click the link below to create a new password:

{reset_link}

This link will expire in {expiry_minutes} minutes.

If you didn't request this password reset, you can safely ignore this email.

© 2026 EmoraTest. All rights reserved.
"""

        return await self.send_email(to, subject, html_content, text_content)

    async def send_welcome(
        self,
        to: str,
        shop_domain: str,
    ) -> bool:
        """Send welcome email after signup."""
        subject = "Welcome to EmoraTest!"
        reset_link = f"{settings.FRONTEND_URL}/dashboard"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to EmoraTest</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f6fa;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f6fa; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #007BFF;">EmoraTest</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 600; color: #111318;">Welcome to EmoraTest! 🎉</h2>
                            <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #6B7280;">
                                You're all set up and ready to unlock emotional insights from your website visitors.
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #6B7280;">
                                Your workspace: <strong>{shop_domain}</strong>
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{reset_link}" style="display: inline-block; background: linear-gradient(135deg, #007BFF, #7C3AED); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-size: 15px; font-weight: 600;">
                                            Go to Dashboard
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; text-align: center;">
                            <p style="margin: 0; font-size: 13px; color: #9CA3AF;">
                                &copy; 2026 EmoraTest. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        text_content = f"""
Welcome to EmoraTest!

You're all set up and ready to unlock emotional insights from your website visitors.

Your workspace: {shop_domain}

Go to your dashboard: {reset_link}

© 2026 EmoraTest. All rights reserved.
"""

        return await self.send_email(to, subject, html_content, text_content)

    async def send_verification_email(
        self,
        to: str,
        verification_link: str,
    ) -> bool:
        """Send email verification email."""
        subject = "Verify Your EmoraTest Account"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f6fa;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f6fa; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #007BFF;">EmoraTest</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 600; color: #111318;">Verify Your Email</h2>
                            <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #6B7280;">
                                Thanks for signing up! Click the button below to verify your email address and activate your account.
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{verification_link}" style="display: inline-block; background: #007BFF; color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-size: 15px; font-weight: 600;">
                                            Verify Email Address
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 24px 0 8px 0; font-size: 14px; color: #6B7280;">
                                Or copy and paste this link:
                            </p>
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #007BFF; word-break: break-all;">
                                <a href="{verification_link}" style="color: #007BFF; word-break: break-all;">{verification_link}</a>
                            </p>
                            <p style="margin: 16px 0 8px 0; font-size: 14px; color: #6B7280;">
                                This link expires in 24 hours.
                            </p>
                            <p style="margin: 0; font-size: 14px; color: #6B7280;">
                                If you didn't create an account, you can safely ignore this email.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; text-align: center;">
                            <p style="margin: 0; font-size: 13px; color: #9CA3AF;">
                                &copy; 2026 EmoraTest. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        text_content = f"""
Verify Your EmoraTest Account

Thanks for signing up! Click the link below to verify your email address and activate your account:

{verification_link}

This link expires in 24 hours.

If you didn't create an account, you can safely ignore this email.

© 2026 EmoraTest. All rights reserved.
"""

        return await self.send_email(to, subject, html_content, text_content)

    async def send_alert_notification(
        self,
        to: str,
        alert_name: str,
        emotion: str,
        trigger_value: float,
        threshold: float,
        page_url: str,
        time_window: str,
    ) -> bool:
        """Send alert notification email when emotion threshold is exceeded."""
        # Emoji mapping for emotions
        emotion_emojis = {
            "confusion": "😕",
            "frustration": "😤",
            "delight": "😊",
            "anxiety": "😰",
            "hesitation": "🤔",
            "focus": "🎯",
            "boredom": "😴",
            "satisfaction": "😌",
        }
        emoji = emotion_emojis.get(emotion, "⚠️")

        # Emotion colors
        emotion_colors = {
            "confusion": "#F59E0B",
            "frustration": "#EF4444",
            "delight": "#10B981",
            "anxiety": "#F97316",
            "hesitation": "#8B5CF6",
            "focus": "#3B82F6",
            "boredom": "#6B7280",
            "satisfaction": "#059669",
        }
        color = emotion_colors.get(emotion, "#007BFF")

        dashboard_link = f"{settings.FRONTEND_URL}/dashboard/sessions"

        subject = f"Alert: {emotion.capitalize()} spike detected {emoji}"
        page_display = page_url if page_url != "all pages" else "All pages"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alert Fired</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f6fa;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f6fa; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #007BFF;">EmoraTest Alert</h1>
                        </td>
                    </tr>
                    <!-- Alert Banner -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: {color}; text-align: center;">
                            <span style="font-size: 48px;">{emoji}</span>
                            <h2 style="margin: 10px 0 0 0; font-size: 20px; font-weight: 600; color: #ffffff;">
                                {emotion.capitalize()} Alert Fired
                            </h2>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600; color: #111318;">{alert_name}</h3>
                            <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #6B7280;">
                                Your alert rule has triggered because {emotion} exceeded the threshold.
                            </p>
                            <!-- Stats Grid -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                                <tr>
                                    <td style="padding: 16px; background-color: #f9fafb; border-radius: 8px; text-align: center;">
                                        <div style="font-size: 28px; font-weight: 700; color: {color};">{trigger_value:.1f}%</div>
                                        <div style="font-size: 13px; color: #6B7280; margin-top: 4px;">Current Value</div>
                                    </td>
                                    <td style="width: 12px;"></td>
                                    <td style="padding: 16px; background-color: #f9fafb; border-radius: 8px; text-align: center;">
                                        <div style="font-size: 28px; font-weight: 700; color: #6B7280;">{threshold:.0f}%</div>
                                        <div style="font-size: 13px; color: #6B7280; margin-top: 4px;">Threshold</div>
                                    </td>
                                </tr>
                            </table>
                            <!-- Details -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">
                                        <span style="font-size: 13px; color: #6B7280;">Page</span>
                                        <div style="font-size: 14px; color: #111318; margin-top: 4px;">{page_display}</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">
                                        <span style="font-size: 13px; color: #6B7280;">Time Window</span>
                                        <div style="font-size: 14px; color: #111318; margin-top: 4px;">{time_window}</div>
                                    </td>
                                </tr>
                            </table>
                            <!-- CTA Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{dashboard_link}" style="display: inline-block; background: #007BFF; color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-size: 15px; font-weight: 600;">
                                            View Sessions
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; text-align: center;">
                            <p style="margin: 0; font-size: 13px; color: #9CA3AF;">
                                &copy; 2026 EmoraTest. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        text_content = f"""
EmoraTest Alert: {emotion.capitalize()} spike detected {emoji}

Alert: {alert_name}
Current Value: {trigger_value:.1f}%
Threshold: {threshold:.0f}%
Page: {page_display}
Time Window: {time_window}

View sessions: {dashboard_link}

© 2026 EmoraTest. All rights reserved.
"""

        return await self.send_email(to, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()
