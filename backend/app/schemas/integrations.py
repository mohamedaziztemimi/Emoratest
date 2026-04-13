"""Pydantic schemas for Integration and Webhook CRUD."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ── Types ────────────────────────────────────────────────────

IntegrationType = Literal[
    "slack", "jira", "amplitude", "posthog", "snowflake", "bigquery", "webhook", "zapier"
]

EventType = Literal[
    "experiment.winner",
    "experiment.started",
    "experiment.stopped",
    "test.started",
    "test.stopped",
    "emotion.frustration_spike",
    "anomaly.detected",
    "session.ended",
    "user.churn_risk",
]


# ── Integration CRUD Schemas ─────────────────────────────────────

class IntegrationConfig(BaseModel):
    """Base config schema for integrations."""

    webhook_url: str | None = None
    base_url: str | None = None
    email: str | None = None
    api_token: str | None = None
    project_key: str | None = None
    project_id: str | None = None
    dataset_id: str | None = None
    credentials_json: str | None = None
    account: str | None = None
    user: str | None = None
    password: str | None = None
    database: str | None = None
    schema: str | None = None
    secret: str | None = None
    headers: dict[str, str] | None = None


class IntegrationCreateRequest(BaseModel):
    """Request to create a new integration."""

    name: str = Field(..., min_length=1, max_length=255)
    integration_type: IntegrationType
    config: IntegrationConfig
    events: list[EventType] = Field(default_factory=list)


class IntegrationUpdateRequest(BaseModel):
    """Request to update an integration."""

    name: str | None = Field(None, min_length=1, max_length=255)
    config: IntegrationConfig | None = None
    events: list[EventType] | None = None
    enabled: bool | None = None


class IntegrationOut(BaseModel):
    """Integration response."""

    id: str
    workspace_id: str
    name: str
    integration_type: IntegrationType
    events: list[EventType]
    enabled: bool
    last_triggered_at: datetime | None
    failure_count: int
    created_at: datetime | None
    updated_at: datetime | None
    config: dict | None


class IntegrationListResponse(BaseModel):
    """List of integrations."""

    integrations: list[IntegrationOut]
    total: int


# ── Webhook Log Schemas ─────────────────────────────────────

class WebhookLogOut(BaseModel):
    """Webhook log entry."""

    id: str
    integration_id: str
    event_type: EventType
    response_status: int
    duration_ms: int
    created_at: datetime | None
    payload: dict | None


class WebhookLogListResponse(BaseModel):
    """List of webhook logs."""

    logs: list[WebhookLogOut]
    total: int


# ── Test Schemas ─────────────────────────────────────────────

class IntegrationTestRequest(BaseModel):
    """Request to test an integration."""

    event_type: EventType
    payload: dict = Field(
        default_factory=lambda: {
            "test": True,
            "timestamp": "2026-01-01T00:00:00Z",
        }
    )


class IntegrationTestResponse(BaseModel):
    """Response from integration test."""

    success: bool
    message: str
    status_code: int | None = None
    duration_ms: int | None = None


# ── Dispatch Schemas ─────────────────────────────────────────

class EventDispatchRequest(BaseModel):
    """Request to manually dispatch an event."""

    event_type: EventType
    payload: dict


class EventDispatchResult(BaseModel):
    """Result from dispatching to a single integration."""

    integration_id: str
    success: bool
    status_code: int | None = None
    duration_ms: int | None = None
    error: str | None = None


class EventDispatchResponse(BaseModel):
    """Response from dispatching to integrations."""

    dispatched: int
    success: int
    failed: int
    results: list[EventDispatchResult]


# ── Inbound Webhook Schemas ─────────────────────────────────

class InboundWebhookResponse(BaseModel):
    """Response from inbound webhook processing."""

    status: str
    message: str
    data: dict | None = None


class ZapierTriggerResponse(BaseModel):
    """Response from Zapier poll trigger."""

    data: list[dict]
    timestamp: str
    message: str
