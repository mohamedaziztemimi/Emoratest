"""SDK API endpoints — session and event ingestion (CONV-34).

Endpoints:
    POST   /api/v1/sessions              — create a new tracking session
    PUT    /api/v1/sessions/{id}/end      — end a session
    PUT    /api/v1/sessions/{id}/outcome  — report conversion outcome
    POST   /api/v1/events/batch           — ingest a batch of events
"""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import case, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.event import Event
from app.models.merchant import Merchant
from app.models.session import Session
from app.schemas.sdk import (
    EventBatchRequest,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionOutcomeRequest,
)


async def get_merchant_from_sdk_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Merchant:
    """Auth via X-SDK-Key header ONLY (ignores cookie).

    This ensures consistent merchant identification for SDK requests,
    avoiding conflicts with browser auth cookies.
    """
    # Try header first
    sdk_key = request.headers.get("X-SDK-Key")

    # Fallback to query param (for sendBeacon)
    if not sdk_key:
        sdk_key = request.query_params.get("sdk_key")

    print(f"[DEBUG] get_merchant_from_sdk_key: sdk_key_present={bool(sdk_key)}, path={request.url.path}")

    if not sdk_key:
        raise HTTPException(
            status_code=401,
            detail="X-SDK-Key header is required",
        )

    key_hash = hashlib.sha256(sdk_key.encode()).hexdigest()
    result = await db.execute(
        select(Merchant).where(
            Merchant.sdk_key_hash == key_hash,
            Merchant.is_active.is_(True),
        )
    )
    merchant = result.scalar_one_or_none()

    if merchant:
        print(f"[DEBUG] Found merchant: id={merchant.id}")
    else:
        print(f"[DEBUG] No merchant found for sdk_key_hash={key_hash}")

    if not merchant:
        raise HTTPException(status_code=401, detail="Invalid SDK key")

    return merchant

router = APIRouter(tags=["sdk"])


# ── Health check (debug) ────────────────────────────────────────

@router.get("/health")
async def sdk_health():
    """Debug endpoint to verify SDK router is loaded."""
    return {"status": "SDK router is working"}


# ── Session endpoints ──────────────────────────────────────────


@router.post("/sessions", response_model=SessionCreateResponse)
@limiter.limit("2000/minute")
async def create_session(
    request: Request,
    body: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_from_sdk_key),
):
    """Create a new tracking session for the authenticated merchant.
    Merchant is identified via X-SDK-Key header, not request body.
    """

    session_id = uuid.uuid4()
    now = datetime.now(UTC)

    # DEBUG: Log session creation
    print(f"[DEBUG] Creating session: id={session_id}, merchant_id={merchant.id}, sdk_key_header={request.headers.get('X-SDK-Key', 'missing')}")

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
    merchant: Merchant = Depends(get_merchant_from_sdk_key),
):
    """Mark a session as ended (set ended_at to now)."""

    try:
        sid = uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session ID") from exc

    # Auto-set outcome to "abandon" if still unknown (user left without buying)
    result = await db.execute(
        update(Session)
        .where(Session.id == sid, Session.merchant_id == merchant.id)
        .values(
            ended_at=datetime.now(UTC),
            outcome=case(
                (Session.outcome == "unknown", "abandon"),
                else_=Session.outcome,
            )
        )
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
    merchant: Merchant = Depends(get_merchant_from_sdk_key),
):
    """Report a conversion outcome for a session."""

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

    # Session outcome updated — trigger full ML scoring pipeline (CONV-35)
    from app.services.feature_worker import enqueue_session_processing

    enqueue_session_processing(session_id)

    return {"status": "updated", "outcome": body.outcome}


@router.post("/sessions/{session_id}/close")
@limiter.limit("2000/minute")
async def close_session(
    request: Request,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_from_sdk_key),
):
    """Combined endpoint for beforeunload — ends session and sets outcome to 'abandon'.

    Accepts sdk_key as query parameter for sendBeacon compatibility.
    This is more reliable than making two separate beacon calls.
    """
    try:
        sid = uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session ID") from exc

    now = datetime.now(UTC)

    result = await db.execute(
        update(Session)
        .where(
            Session.id == sid,
            Session.merchant_id == merchant.id,
        )
        .values(
            ended_at=now,
            outcome=case(
                (Session.outcome == "unknown", "abandon"),
                else_=Session.outcome,
            ),
        )
        .returning(Session.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.commit()

    # Trigger emotion processing
    from app.services.feature_worker import enqueue_session_processing

    enqueue_session_processing(session_id)

    return {"status": "closed"}


# ── Event ingestion ────────────────────────────────────────────


@router.post("/events/batch")
@limiter.limit("2000/minute")
async def ingest_events(
    request: Request,
    body: EventBatchRequest,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_from_sdk_key),
):
    """Ingest a batch of behavioral events for a session.
    Auto-creates session if it doesn't exist (defensive fallback).
    """

    # DEBUG: Log what we're looking for
    print(f"[DEBUG] Events/batch: session_id={body.session_id}, merchant_id={merchant.id}")

    # Verify session belongs to this merchant
    try:
        sid = uuid.UUID(body.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session ID") from exc

    result = await db.execute(
        select(Session.id, Session.merchant_id).where(
            Session.id == sid
        )
    )
    session = result.first()

    # Auto-create session if not found (defensive programming)
    if session is None:
        print(f"[DEBUG] Session {sid} not found — auto-creating for merchant {merchant.id}")
        now = datetime.now(UTC)
        new_session = Session(
            id=sid,
            merchant_id=merchant.id,
            page_url=body.page_url or "unknown",
            started_at=now,
            outcome="unknown",
            country_code=None,
            device_type=None,
            expires_at=now + timedelta(days=90),
        )
        db.add(new_session)
        await db.commit()
        print(f"[DEBUG] Auto-created session {sid} for merchant {merchant.id}")
    else:
        session_merchant_id = session[1]
        print(f"[DEBUG] Session found: merchant_id={session_merchant_id}, expected={merchant.id}")

        if session_merchant_id != merchant.id:
            print(f"[DEBUG] Merchant mismatch! session={session_merchant_id}, auth={merchant.id}")
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
