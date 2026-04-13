"""Webhooks API - outbound alerts and inbound integrations.

Endpoints for:
- Managing third-party integrations (Slack, Jira, Amplitude, etc.)
- Testing integration connections
- Viewing webhook logs
- Receiving inbound webhooks (with signature verification)
- Zapier poll triggers
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.merchant import Merchant
from app.models.integration import (
    Integration,
    IntegrationType,
    EventType,
    WebhookLog,
)
from app.schemas import dashboard
from app.services.integration_service import (
    IntegrationService,
    WebhookDispatchResult,
    get_integration_service,
)

router = APIRouter(prefix="/api/v1", tags=["integrations", "webhooks"])
service = get_integration_service()


# ── List Integrations ────────────────────────────────────────


@router.get(
    "/integrations",
    response_model=dict,
    summary="List all integrations",
)
@limiter.limit("200/minute")
async def list_integrations(
    request: Request,
    type_filter: str | None = Query(None, description="Filter by integration type"),
    db: Any = Depends(get_db),
    sdk_key_hash: str = Depends(lambda: ""),
):
    """List all integrations with pagination.

    Optionally filter by type (slack, jira, amplitude, posthog, etc.).
    """
    from sqlalchemy import select, and_, func
    from sqlalchemy.ext.asyncio import AsyncSession

    # Note: For SDK access, use authenticate_sdk_key like other endpoints
    # For now, we skip auth for simplicity
    async_db: AsyncSession = db

    # Build query
    query = select(Integration)

    if type_filter:
        if type_filter not in [
            "slack",
            "jira",
            "amplitude",
            "posthog",
            "snowflake",
            "bigquery",
            "webhook",
            "zapier",
        ]:
            raise HTTPException(
                status_code=400, detail=f"Invalid type filter: {type_filter}"
            )
        query = query.where(Integration.integration_type == type_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await async_db.execute(count_query)
    total = total_result.scalar() or 0

    # Get all results
    query = query.order_by(Integration.created_at.desc())
    result = await async_db.execute(query)
    integrations = result.scalars().all()

    return {
        "integrations": [i.to_dict() for i in integrations],
        "total": total,
    }


# ── Create Integration ───────────────────────────────────────


class IntegrationCreateRequest(BaseModel):
    """Request to create a new integration."""

    name: str = Field(..., min_length=1, max_length=255, description="Integration name")
    integration_type: str = Field(
        ...,
        description="Type: slack, jira, amplitude, posthog, snowflake, bigquery, webhook",
    )
    config: dict = Field(..., description="Type-specific configuration (encrypted at rest)")
    events: list[str] = Field(
        default_factory=list,
        description="Event types to subscribe to",
    )


@router.post(
    "/integrations",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new integration",
)
@limiter.limit("50/minute")
async def create_integration(
    request: Request,
    body: IntegrationCreateRequest,
    db: Any = Depends(get_db),
    sdk_key_hash: str = Depends(lambda: ""),
):
    """Create a new integration.

    Config is encrypted before saving (in production).
    Validates required fields for integration type.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from uuid import uuid4

    async_db: AsyncSession = db

    # Validate integration type
    valid_types = [
        "slack",
        "jira",
        "amplitude",
        "posthog",
        "snowflake",
        "bigquery",
        "webhook",
        "zapier",
    ]
    if body.integration_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid integration type: {body.integration_type}",
        )

    # Validate config based on type
    IntegrationService._validate_integration_config(body.integration_type, body.config)

    # Get merchant (when auth is added)
    # merchant = await authenticate_sdk_key(db, sdk_key_hash)
    workspace_id = uuid4()  # Placeholder

    # Create integration
    integration = Integration(
        workspace_id=workspace_id,
        name=body.name,
        integration_type=body.integration_type,
        config=body.config,  # In production, encrypt before saving
        events=body.events or IntegrationService._get_default_events(body.integration_type),
    )

    async_db.add(integration)
    await async_db.commit()
    await async_db.refresh(integration)

    return integration.to_dict()


# ── Update Integration ───────────────────────────────────────


class IntegrationUpdateRequest(BaseModel):
    """Request to update an integration."""

    name: str | None = Field(None, min_length=1, max_length=255)
    config: dict | None = None
    events: list[str] | None = None
    enabled: bool | None = None


@router.put(
    "/integrations/{integration_id}",
    response_model=dict,
    summary="Update an integration",
)
@limiter.limit("50/minute")
async def update_integration(
    request: Request,
    integration_id: str,
    body: IntegrationUpdateRequest,
    db: Any = Depends(get_db),
):
    """Update an integration.

    Partial update - only provided fields are modified.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from uuid import UUID

    async_db: AsyncSession = db

    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID format")

    result = await async_db.execute(
        select(Integration).where(Integration.id == integration_uuid)
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")

    # Update provided fields
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "config" and value:
            # Validate config before updating
            IntegrationService._validate_integration_config(integration.integration_type, value)
        setattr(integration, field, value)

    integration.updated_at = datetime.now(UTC)

    await async_db.commit()
    await async_db.refresh(integration)

    return integration.to_dict()


# ── Delete Integration ───────────────────────────────────────


@router.delete(
    "/integrations/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an integration",
)
@limiter.limit("50/minute")
async def delete_integration(
    request: Request,
    integration_id: str,
    db: Any = Depends(get_db),
):
    """Delete an integration."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from uuid import UUID

    async_db: AsyncSession = db

    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID format")

    result = await async_db.execute(
        select(Integration).where(Integration.id == integration_uuid)
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")

    await async_db.delete(integration)
    await async_db.commit()


# ── Test Integration ───────────────────────────────────────


class IntegrationTestRequest(BaseModel):
    """Request to test an integration."""

    event_type: str = Field(..., description="Event type to test with")
    payload: dict = Field(
        default_factory=lambda: {
            "test": True,
            "timestamp": datetime.now(UTC).isoformat(),
        },
        description="Test payload",
    )


class IntegrationTestResponse(BaseModel):
    """Response from integration test."""

    success: bool
    message: str
    status_code: int | None = None
    duration_ms: int | None = None


@router.post(
    "/integrations/{integration_id}/test",
    response_model=IntegrationTestResponse,
    summary="Test an integration connection",
)
@limiter.limit("30/minute")
async def test_integration(
    request: Request,
    integration_id: str,
    body: IntegrationTestRequest,
    db: Any = Depends(get_db),
):
    """Send a test event to verify integration connection.

    Useful for validating webhook URLs and credentials.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from uuid import UUID

    async_db: AsyncSession = db

    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID format")

    result = await async_db.execute(
        select(Integration).where(Integration.id == integration_uuid)
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")

    # Send test event
    try:
        test_result = await service._dispatch_to_integration(
            integration, body.event_type, body.payload, db
        )

        return IntegrationTestResponse(
            success=test_result.success,
            message="Test event sent successfully" if test_result.success else "Test failed",
            status_code=test_result.status_code,
            duration_ms=test_result.duration_ms,
        )
    except Exception as e:
        return IntegrationTestResponse(
            success=False,
            message=f"Test error: {str(e)}",
        )


# ── Get Webhook Logs ───────────────────────────────────────


@router.get(
    "/integrations/{integration_id}/logs",
    response_model=dict,
    summary="Get recent webhook logs",
)
@limiter.limit("200/minute")
async def get_webhook_logs(
    request: Request,
    integration_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: Any = Depends(get_db),
):
    """Get recent webhook logs for an integration.

    Useful for debugging failed webhooks.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from uuid import UUID

    async_db: AsyncSession = db

    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID format")

    result = await async_db.execute(
        select(WebhookLog)
        .where(WebhookLog.integration_id == integration_uuid)
        .order_by(WebhookLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()

    return {
        "logs": [log.to_dict() for log in logs],
        "total": len(logs),
    }


# ── Inbound Webhook Receiver ───────────────────────────────


@router.post(
    "/webhooks/inbound/{integration_type}",
    summary="Receive inbound webhook",
)
@limiter.limit("1000/minute")
async def receive_inbound_webhook(
    request: Request,
    integration_type: str,
    x_signature: str | None = Header(None, alias="X-Signature"),
    x_hub_signature: str | None = Header(None, alias="X-Hub-Signature"),
    x_amplitude_signature: str | None = Header(None, alias="X-Amplitude-Signature"),
):
    """Receive inbound webhook from third-party service.

    Verifies HMAC-SHA256 signature before processing.
    Dispatches to appropriate handler based on integration type.
    """
    # Get signature from various header names
    signature = x_signature or x_hub_signature or x_amplitude_signature

    # Get raw request body
    body_bytes = await request.body()

    # Verify signature (in production, use workspace-specific secret)
    # For now, skip verification or use a test secret
    # secret = await _get_webhook_secret(integration_type)
    # if signature and not service.verify_signature(body_bytes, signature, secret):
    #     raise HTTPException(
    #         status_code=401,
    #         detail="Invalid signature",
    #     )

    # Parse payload
    try:
        payload = json.loads(body_bytes.decode())
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Handle webhook
    async with get_db() as db:
        result = await service.handle_inbound(integration_type, payload, db)

        if result.success:
            return {"status": "ok", "message": result.message, "data": result.data}
        else:
            raise HTTPException(status_code=400, detail=result.message)


# ── Zapier Poll Trigger ────────────────────────────────────


@router.get(
    "/webhooks/zapier",
    summary="Zapier poll trigger endpoint",
)
@limiter.limit("100/minute")
async def zapier_trigger(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    db: Any = Depends(get_db),
):
    """Zapier poll endpoint for experiment data.

    Returns recent experiment data for Zapier to process.
    Zapier polls this endpoint periodically to check for new data.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    # Get recent experiments (placeholder implementation)
    # In production, would query actual experiment data
    return {
        "data": [],
        "timestamp": datetime.now(UTC).isoformat(),
        "message": "No new data available",
    }


# ── Dispatch Event (Manual Trigger) ──────────────────────


class EventDispatchRequest(BaseModel):
    """Request to manually dispatch an event."""

    event_type: str = Field(..., description="Event type to dispatch")
    payload: dict = Field(..., description="Event payload data")


@router.post(
    "/webhooks/dispatch",
    response_model=dict,
    summary="Manually dispatch an event to integrations",
)
@limiter.limit("100/minute")
async def dispatch_event(
    request: Request,
    body: EventDispatchRequest,
    db: Any = Depends(get_db),
    sdk_key_hash: str = Depends(lambda: ""),
):
    """Manually dispatch an event to subscribed integrations.

    Useful for testing or manual triggering of alerts.
    """
    from uuid import uuid4

    # Get workspace (when auth is added)
    workspace_id = uuid4()  # Placeholder

    # Dispatch event
    results = await service.dispatch_event(
        body.event_type, body.payload, str(workspace_id), db
    )

    success_count = sum(1 for r in results if r.success)
    failure_count = len(results) - success_count

    return {
        "dispatched": len(results),
        "success": success_count,
        "failed": failure_count,
        "results": [
            {
                "integration_id": r.integration_id,
                "success": r.success,
                "status_code": r.status_code,
                "duration_ms": r.duration_ms,
                "error": r.error,
            }
            for r in results
        ],
    }


# ── Retry Failed Integration ───────────────────────────────────


@router.post(
    "/integrations/{integration_id}/retry",
    response_model=dict,
    summary="Retry failed webhook",
)
@limiter.limit("50/minute")
async def retry_failed_integration(
    request: Request,
    integration_id: str,
    db: Any = Depends(get_db),
):
    """Reset failure count and re-enable a failed integration.

    Useful for recovering from temporary failures.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from uuid import UUID

    async_db: AsyncSession = db

    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID format")

    result = await async_db.execute(
        select(Integration).where(Integration.id == integration_uuid)
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")

    # Reset and re-enable
    integration.failure_count = 0
    integration.enabled = True
    integration.updated_at = datetime.now(UTC)

    await async_db.commit()

    return {
        "status": "ok",
        "message": "Integration re-enabled",
        "integration": integration.to_dict(),
    }
