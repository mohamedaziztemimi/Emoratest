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

    sdk_key_hash = hashlib.sha256(sdk_key.encode()).hexdigest()
    result = await db.execute(
        select(Merchant).where(
            Merchant.sdk_key_hash == sdk_key_hash,
            Merchant.is_active.is_(True),
        )
    )
    merchant = result.scalar_one_or_none()

    if not merchant:
        raise HTTPException(status_code=401, detail="Invalid SDK key")

    return merchant


def _is_ipv4(ip: str) -> bool:
    """Check if the given string is a valid IPv4 address."""
    if not ip:
        return False
    # IPv4 contains dots and not colons
    parts = ip.strip().split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def _is_cloudflare_ip(ip: str) -> bool:
    """Check if IP is a Cloudflare proxy IP (should be skipped)."""
    if not ip or not _is_ipv4(ip):
        return False
    # Cloudflare IP ranges (simplified check)
    # 172.64.0.0/13, 162.158.0.0/15, 104.16.0.0/13, etc.
    parts = ip.strip().split(".")
    if len(parts) != 4:
        return False
    try:
        first = int(parts[0])
        second = int(parts[1])
        # 172.64.x.x - 172.71.x.x (Cloudflare)
        if first == 172 and 64 <= second <= 71:
            return True
        # 162.158.x.x - 162.159.x.x (Cloudflare)
        if first == 162 and second in [158, 159]:
            return True
        # 104.16.x.x - 104.23.x.x (Cloudflare)
        if first == 104 and 16 <= second <= 23:
            return True
        # 188.114.x.x (Cloudflare)
        if first == 188 and second == 114:
            return True
    except ValueError:
        pass
    return False


def extract_client_ip(request: Request) -> str | None:
    """Extract client IP from request headers, accounting for proxies.

    Priority order:
    1. CF-Connecting-IP (Cloudflare) - most reliable if Cloudflare is used
    2. X-Forwarded-For first IP (original client, leftmost)
    3. X-Real-IP (nginx/Caddy reverse proxy)

    NEVER uses request.client.host as it's usually the proxy IP (Cloudflare, etc.)

    Always prefers IPv4 over IPv6 when available.
    Skips known Cloudflare proxy IPs.

    Returns None if no IP can be determined.
    """
    # 1. Cloudflare Connecting IP - most reliable when behind Cloudflare
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        cf_ip = cf_ip.strip()
        # CF-Connecting-IP can contain multiple IPs (rare), take first
        first_cf = cf_ip.split(",")[0].strip()
        if _is_ipv4(first_cf):
            return first_cf
        # If CF returned IPv6, try to get IPv4 from other headers
        if first_cf and ":" in first_cf:
            # Got IPv6 from CF, but prefer IPv4 from other headers
            pass
        elif first_cf:
            return first_cf

    # 2. X-Forwarded-For - format: "client IP, proxy1, proxy2, ..."
    # The LEFTMOST IP is the original client
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        xff_ips = [ip.strip() for ip in xff.split(",")]
        for ip in xff_ips:
            # Return the first IPv4 found that's NOT a Cloudflare IP
            if _is_ipv4(ip) and not _is_cloudflare_ip(ip):
                return ip
        # No valid IPv4 in XFF, return first non-Cloudflare IP (might be IPv6)
        for ip in xff_ips:
            if not _is_cloudflare_ip(ip):
                return ip
        # All IPs are Cloudflare, return first one anyway
        if xff_ips:
            return xff_ips[0]

    # 3. X-Real-IP - set by nginx/Caddy, usually the real client IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        real_ip = real_ip.strip()
        if _is_ipv4(real_ip) and not _is_cloudflare_ip(real_ip):
            return real_ip
        if real_ip and not _is_cloudflare_ip(real_ip):
            return real_ip

    # 4. Direct connection - ONLY as last resort, and check for Cloudflare IPs
    if request.client and request.client.host:
        host = request.client.host.strip()
        if _is_ipv4(host) and not _is_cloudflare_ip(host):
            return host
        if host and not _is_cloudflare_ip(host):
            return host

    return None

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
    Enforces monthly session limits.
    """
    now = datetime.now(UTC)
    current_month = now.month
    current_year = now.year

    # Reset session count if month has changed
    if merchant.session_month != current_month or merchant.session_year != current_year:
        from sqlalchemy import update as sql_update
        await db.execute(
            sql_update(Merchant)
            .where(Merchant.id == merchant.id)
            .values(sessions_this_month=0, session_month=current_month, session_year=current_year)
        )
        merchant.sessions_this_month = 0
        merchant.session_month = current_month
        merchant.session_year = current_year

    # Check session limit
    if merchant.sessions_this_month >= merchant.monthly_session_limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "session_limit_reached",
                "message": "Monthly session limit reached",
                "limit": merchant.monthly_session_limit,
                "used": merchant.sessions_this_month,
            },
        )

    session_id = uuid.uuid4()

    # Extract IP address and user agent
    client_ip = extract_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    # DEBUG: Log all IP-related headers to diagnose IP capture issues
    print(f"[DEBUG IP] Captured IP: {client_ip}")
    print(f"[DEBUG IP] CF-Connecting-IP: {request.headers.get('CF-Connecting-IP')}")
    print(f"[DEBUG IP] X-Forwarded-For: {request.headers.get('X-Forwarded-For')}")
    print(f"[DEBUG IP] X-Real-IP: {request.headers.get('X-Real-IP')}")
    print(f"[DEBUG IP] request.client.host: {request.client.host if request.client else 'N/A'}")

    session = Session(
        id=session_id,
        merchant_id=merchant.id,
        page_url=body.page_url,
        started_at=body.started_at,
        outcome="unknown",
        country_code=body.country_code,
        device_type=body.device_type,
        expires_at=now + timedelta(days=90),
        ip_address=client_ip,
        user_agent=user_agent,
    )

    db.add(session)

    # Increment session count
    from sqlalchemy import update as sql_update
    await db.execute(
        sql_update(Merchant)
        .where(Merchant.id == merchant.id)
        .values(sessions_this_month=Merchant.sessions_this_month + 1)
    )

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
    Updates session page_url, IP, country, and ended_at on each event batch.
    """

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

    now = datetime.now(UTC)

    # BUG 5: Extract IP address and country code from headers
    client_ip = extract_client_ip(request)
    country_code = request.headers.get("CF-IPCountry")  # Cloudflare provides 2-letter country code

    # BUG 3: Get page_url from body or use Referer header as fallback
    page_url = body.page_url
    if not page_url or page_url == "unknown":
        referer = request.headers.get("Referer")
        if referer:
            page_url = referer
    if not page_url:
        page_url = "unknown"

    # Auto-create session if not found (defensive programming)
    if session is None:
        new_session = Session(
            id=sid,
            merchant_id=merchant.id,
            page_url=page_url,
            started_at=now,
            outcome="unknown",
            country_code=country_code,
            device_type=None,
            expires_at=now + timedelta(days=90),
            ip_address=client_ip,
        )
        db.add(new_session)
        await db.commit()
    else:
        session_merchant_id = session[1]

        if session_merchant_id != merchant.id:
            raise HTTPException(status_code=404, detail="Session not found")

        # BUG 4: Update ended_at timestamp when new events arrive (keeps session duration current)
        # BUG 3 & 5: Also update page_url, IP, and country if they were previously unknown
        await db.execute(
            update(Session)
            .where(Session.id == sid)
            .values(
                ended_at=now,
                page_url=page_url if Session.page_url == "unknown" or not Session.page_url else Session.page_url,
                ip_address=client_ip if not Session.ip_address else Session.ip_address,
                country_code=country_code if not Session.country_code else Session.country_code,
            )
        )
        await db.commit()

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
            # Semantic enrichment fields
            label=getattr(e, "label", None),
            element_type=getattr(e, "element_type", None),
            section=getattr(e, "section", None),
            selector=getattr(e, "selector", None),
        )
        for e in body.events
    ]

    db.add_all(events)
    await db.commit()

    # Enqueue background feature processing (CONV-34)
    from app.services.feature_worker import enqueue_session_processing

    enqueue_session_processing(body.session_id)

    # Enrich events with human-readable descriptions (non-blocking, UI-only)
    # This does NOT affect ML pipeline - only creates enriched records for UI
    from app.services.event_enrichment import enrich_events
    import asyncio

    # Fire and forget - don't block event ingestion
    async def enrich_later():
        try:
            async with get_db() as enrich_db:
                await enrich_events(enrich_db, body.session_id, events)
        except Exception:
            pass  # Enrichment failures should not break event ingestion

    asyncio.create_task(enrich_later())

    return {"status": "ok", "count": len(events)}
