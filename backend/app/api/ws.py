"""Real-Time WebSocket Scoring API (CONV-42).

Provides a WebSocket endpoint that pushes live session scoring updates
to connected dashboard clients. Each connection is authenticated and
merchant-scoped.

Protocol:
    1. Client connects to /api/v1/ws/scores?sdk_key=<hash>
    2. Server validates SDK key against merchants table
    3. Client sends JSON: {"action": "subscribe", "session_ids": ["uuid", ...]}
    4. Server pushes scoring updates as they complete
    5. Client can send {"action": "ping"} to keep connection alive
    6. Server sends {"action": "pong"} in response

Security:
    - SDK key validated on connect (rejects 4001 if invalid)
    - Merchant can only subscribe to their own sessions
    - Connection auto-closes after 30 minutes idle
    - Max 10 subscribed sessions per connection
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.merchant import Merchant
from app.models.session import Session

logger = logging.getLogger("conversiono.ws")

router = APIRouter(tags=["websocket"])

# In-memory registry of active connections
# Maps merchant_id -> list of (websocket, subscribed_session_ids)
_connections: dict[str, list[tuple[WebSocket, set[str]]]] = {}

# Limits
MAX_SUBSCRIPTIONS_PER_CONNECTION = 10
IDLE_TIMEOUT_S = 1800  # 30 minutes
HEARTBEAT_INTERVAL_S = 30


async def _authenticate_ws(sdk_key: str) -> Merchant | None:
    """Validate SDK key and return merchant or None."""
    async with async_session() as db:
        result = await db.execute(
            select(Merchant).where(
                Merchant.sdk_key_hash == sdk_key,
                Merchant.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()


async def _validate_session_ownership(
    merchant_id: uuid.UUID, session_ids: list[str]
) -> list[str]:
    """Return only session IDs that belong to the merchant."""
    valid = []
    async with async_session() as db:
        for sid_str in session_ids:
            try:
                sid = uuid.UUID(sid_str)
            except ValueError:
                continue
            result = await db.execute(
                select(Session.id).where(
                    Session.id == sid, Session.merchant_id == merchant_id
                )
            )
            if result.scalar_one_or_none() is not None:
                valid.append(sid_str)
    return valid


@router.websocket("/ws/scores")
async def websocket_scores(websocket: WebSocket):
    """WebSocket endpoint for real-time session scoring updates."""
    # Extract SDK key from query params
    sdk_key = websocket.query_params.get("sdk_key")
    if not sdk_key:
        await websocket.close(code=4001, reason="Missing sdk_key parameter")
        return

    # Authenticate
    merchant = await _authenticate_ws(sdk_key)
    if merchant is None:
        await websocket.close(code=4001, reason="Invalid or inactive SDK key")
        return

    await websocket.accept()

    merchant_key = str(merchant.id)
    subscribed_sessions: set[str] = set()

    # Register connection
    if merchant_key not in _connections:
        _connections[merchant_key] = []
    _connections[merchant_key].append((websocket, subscribed_sessions))

    try:
        await websocket.send_json({
            "action": "connected",
            "merchant_id": merchant_key,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        while True:
            try:
                raw = await asyncio.wait_for(
                    websocket.receive_text(), timeout=IDLE_TIMEOUT_S
                )
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "action": "timeout",
                    "reason": "idle_timeout",
                })
                break

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "action": "error",
                    "detail": "Invalid JSON",
                })
                continue

            action = msg.get("action")

            if action == "ping":
                await websocket.send_json({"action": "pong"})

            elif action == "subscribe":
                session_ids = msg.get("session_ids", [])
                if not isinstance(session_ids, list):
                    await websocket.send_json({
                        "action": "error",
                        "detail": "session_ids must be a list",
                    })
                    continue

                # Enforce limit
                if len(session_ids) > MAX_SUBSCRIPTIONS_PER_CONNECTION:
                    await websocket.send_json({
                        "action": "error",
                        "detail": f"Max {MAX_SUBSCRIPTIONS_PER_CONNECTION} subscriptions",
                    })
                    continue

                # Validate ownership
                valid_ids = await _validate_session_ownership(
                    merchant.id, session_ids
                )
                subscribed_sessions.clear()
                subscribed_sessions.update(valid_ids)

                await websocket.send_json({
                    "action": "subscribed",
                    "session_ids": list(subscribed_sessions),
                    "count": len(subscribed_sessions),
                })

            elif action == "unsubscribe":
                subscribed_sessions.clear()
                await websocket.send_json({"action": "unsubscribed"})

            else:
                await websocket.send_json({
                    "action": "error",
                    "detail": f"Unknown action: {action}",
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for merchant %s", merchant_key)
    except Exception:
        logger.exception("WebSocket error for merchant %s", merchant_key)
    finally:
        # Unregister
        if merchant_key in _connections:
            _connections[merchant_key] = [
                (ws, sids)
                for ws, sids in _connections[merchant_key]
                if ws is not websocket
            ]
            if not _connections[merchant_key]:
                del _connections[merchant_key]


async def broadcast_scoring_update(
    merchant_id: str, session_id: str, scores: dict
) -> int:
    """Push a scoring update to all connected clients subscribed to this session.

    Called by the feature worker after ML scoring completes.
    Returns the number of clients notified.
    """
    conns = _connections.get(merchant_id, [])
    notified = 0

    payload = {
        "action": "score_update",
        "session_id": session_id,
        "scores": scores,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    for ws, subscribed in conns:
        if session_id in subscribed:
            try:
                await ws.send_json(payload)
                notified += 1
            except Exception:
                logger.debug("Failed to send WS update to client")

    return notified
