"""SDK API endpoints — session and event ingestion (CONV-34).

Endpoints:
    POST   /api/v1/sessions              — create a new tracking session
    PUT    /api/v1/sessions/{id}/end      — end a session
    PUT    /api/v1/sessions/{id}/outcome  — report conversion outcome
    POST   /api/v1/events/batch           — ingest a batch of events
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.event import Event
from app.models.session import Session
from app.schemas.sdk import (
    EventBatchRequest,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionOutcomeRequest,
)
from app.services.sdk_auth import authenticate_sdk_key, get_sdk_key_header

router = APIRouter(tags=["sdk"])


# ── Session endpoints ──────────────────────────────────────────


@router.post("/sessions", response_model=SessionCreateResponse)
@limiter.limit("2000/minute")
async def create_session(
    request: Request,
    body: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    sdk_key: str = Depends(get_sdk_key_header),
):
    """Create a new tracking session for the authenticated merchant.
    Merchant is identified via X-SDK-Key header, not request body.
    """
    merchant = await authenticate_sdk_key(db, sdk_key)

    session_id = uuid.uuid4()
    now = datetime.now(UTC)

    session = Session(
        id=session_id,
        merchant_id=merchant.id,
        page_url=body.page_url,
        started_at=body.started_at,
        outcome="unknown",
        country_code=body.country_code,
        device_type=body.device_type,
        expires_at=now + timedelta(days=90),
    )

    db.add(session)
    await db.commit()

    return SessionCreateResponse(session_id=str(session_id))


@router.put("/sessions/{session_id}/end")
@limiter.limit("2000/minute")
async def end_session(
    request: Request,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    sdk_key: str = Depends(get_sdk_key_header),
):
    """Mark a session as ended (set ended_at to now)."""
    merchant = await authenticate_sdk_key(db, sdk_key)

    try:
        sid = uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session ID") from exc

    result = await db.execute(
        update(Session)
        .where(Session.id == sid, Session.merchant_id == merchant.id)
        .values(ended_at=datetime.now(UTC))
        .returning(Session.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.commit()

    # Session ended — trigger full ML scoring pipeline (CONV-35)
    from app.services.feature_worker import enqueue_session_processing

    enqueue_session_processing(session_id)

    return {"status": "ended"}


@router.put("/sessions/{session_id}/outcome")
@limiter.limit("2000/minute")
async def update_outcome(
    request: Request,
    session_id: str,
    body: SessionOutcomeRequest,
    db: AsyncSession = Depends(get_db),
    sdk_key: str = Depends(get_sdk_key_header),
):
    """Report a conversion outcome for a session."""
    merchant = await authenticate_sdk_key(db, sdk_key)

    try:
        sid = uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session ID") from exc

    result = await db.execute(
        update(Session)
        .where(Session.id == sid, Session.merchant_id == merchant.id)
        .values(outcome=body.outcome)
        .returning(Session.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.commit()
    return {"status": "updated", "outcome": body.outcome}


# ── Event ingestion ────────────────────────────────────────────


@router.post("/events/batch")
@limiter.limit("2000/minute")
async def ingest_events(
    request: Request,
    body: EventBatchRequest,
    db: AsyncSession = Depends(get_db),
    sdk_key: str = Depends(get_sdk_key_header),
):
    """Ingest a batch of behavioral events for a session."""
    merchant = await authenticate_sdk_key(db, sdk_key)

    # Verify session belongs to this merchant
    try:
        sid = uuid.UUID(body.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session ID") from exc

    result = await db.execute(
        select(Session.id).where(
            Session.id == sid, Session.merchant_id == merchant.id
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Bulk insert events
    events = [
        Event(
            session_id=sid,
            type=e.type,
            ts=e.ts,
            x=e.x,
            y=e.y,
            velocity=e.velocity,
            element_id=e.element_id,
            metadata_=e.metadata,
        )
        for e in body.events
    ]

    db.add_all(events)
    await db.commit()

    # Enqueue background feature processing (CONV-34)
    from app.services.feature_worker import enqueue_session_processing

    enqueue_session_processing(body.session_id)

    return {"status": "ok", "count": len(events)}
