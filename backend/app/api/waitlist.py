"""Waitlist API endpoints — for users interested in paid plans."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.waitlist import WaitlistEntry

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
