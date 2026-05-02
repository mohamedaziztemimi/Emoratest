"""Waitlist API endpoints — for users interested in paid plans."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.waitlist import WaitlistEntry
from app.services.email import email_service

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


# ── Schemas ─────────────────────────────────────────────────────


class WaitlistRequest(BaseModel):
    email: EmailStr
    company_name: str | None = None
    plan_interest: str = "growth"
    current_sessions_monthly: int | None = None
    message: str | None = None


class WaitlistResponse(BaseModel):
    success: bool
    message: str


# ── Helper: Send waitlist notification email ─────────────────────


async def _send_waitlist_notification(entry: WaitlistEntry) -> None:
    """Send notification email to hello@emoratest.com when someone joins waitlist."""
    sessions_info = (
        f"{entry.current_sessions_monthly:,} sessions/month"
        if entry.current_sessions_monthly
        else "Not specified"
    )

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Waitlist Signup</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f6fa;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f6fa; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center; border-bottom: 1px solid #e5e7eb; background: linear-gradient(135deg, #007BFF 0%, #7C3AED 100%);">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #ffffff;">🎉 New Waitlist Signup</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 24px 0; font-size: 18px; font-weight: 600; color: #111318;">Someone just joined the EmoraTest waitlist!</h2>

                            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #f3f4f6; font-weight: 600; color: #6B7280; width: 140px;">Email</td>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #f3f4f6; color: #111318;"><a href="mailto:{entry.email}" style="color: #007BFF; text-decoration: none;">{entry.email}</a></td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #f3f4f6; font-weight: 600; color: #6B7280;">Company</td>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #f3f4f6; color: #111318;">{entry.company_name or 'Not specified'}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #f3f4f6; font-weight: 600; color: #6B7280;">Plan Interest</td>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #f3f4f6; color: #111318;">{entry.plan_interest.title()}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #f3f4f6; font-weight: 600; color: #6B7280;">Current Volume</td>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #f3f4f6; color: #111318;">{sessions_info}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; font-weight: 600; color: #6B7280; vertical-align: top;">Message</td>
                                    <td style="padding: 12px 0; color: #111318;">{entry.message or 'No message'}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; border-top: 1px solid #f3f4f6; font-weight: 600; color: #6B7280;">Signed up</td>
                                    <td style="padding: 12px 0; border-top: 1px solid #f3f4f6; color: #111318;">{entry.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; text-align: center;">
                            <p style="margin: 0; font-size: 13px; color: #9CA3AF;">
                                View all waitlist entries in the <a href="https://emoratest.com/api/v1/waitlist/admin" style="color: #007BFF; text-decoration: none;">admin panel</a>
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
NEW WAITLIST SIGNUP
{'=' * 40}

Email: {entry.email}
Company: {entry.company_name or 'Not specified'}
Plan Interest: {entry.plan_interest.title()}
Current Volume: {sessions_info}
Message: {entry.message or 'No message'}
Signed up: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC

View all: https://emoratest.com/api/v1/waitlist/admin
"""

    await email_service.send_email(
        to="hello@emoratest.com",
        subject=f"New Waitlist Signup: {entry.email}",
        html_content=html_content,
        text_content=text_content,
    )


# ── POST /waitlist ───────────────────────────────────────────────


@router.post("", response_model=WaitlistResponse)
@limiter.limit("10/minute")
async def join_waitlist(
    body: WaitlistRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add email to waitlist for paid plans.

    No auth required — this is a public endpoint for potential customers.
    Rate-limited to prevent abuse.
    """
    # Check if already on waitlist
    existing = await db.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == body.email)
    )
    if existing.scalar_one_or_none() is not None:
        # Already on waitlist — return success (don't reveal existence)
        return WaitlistResponse(
            success=True,
            message="You're on the list!",
        )

    # Create new waitlist entry
    entry = WaitlistEntry(
        email=body.email,
        company_name=body.company_name,
        plan_interest=body.plan_interest or "growth",
        current_sessions_monthly=body.current_sessions_monthly,
        message=body.message,
        status="pending",
    )

    db.add(entry)
    await db.commit()

    # Send notification email to hello@emoratest.com
    await _send_waitlist_notification(entry)

    return WaitlistResponse(
        success=True,
        message="You're on the list!",
    )


@router.get("/admin")
async def get_waitlist(
    db: AsyncSession = Depends(get_db),
):
    """Get all waitlist entries (admin only).

    TODO: Add admin authentication.
    """
    result = await db.execute(
        select(WaitlistEntry).order_by(WaitlistEntry.created_at.desc())
    )
    entries = result.scalars().all()

    return {
        "entries": [
            {
                "id": str(entry.id),
                "email": entry.email,
                "company_name": entry.company_name,
                "plan_interest": entry.plan_interest,
                "current_sessions_monthly": entry.current_sessions_monthly,
                "message": entry.message,
                "status": entry.status,
                "created_at": entry.created_at,
            }
            for entry in entries
        ]
    }
