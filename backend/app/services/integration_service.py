"""Integration service for outbound webhooks and third-party connections.

Provides:
- Event dispatch to multiple integrations in parallel
- Slack alerts for experiment winners and frustration spikes
- Jira issue creation for detected issues
- Amplitude/PostHog experiment tracking
- Snowflake/BigQuery data warehouse sync
- Inbound webhook verification and handling
- Auto-disable failing integrations
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integration import (
    EventType,
    Integration,
    IntegrationType,
    WebhookLog,
)

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


# ── Result Classes ────────────────────────────────────────────────


@dataclass
class WebhookDispatchResult:
    """Result of dispatching a webhook."""

    integration_id: str
    event_type: str
    success: bool
    status_code: int | None
    duration_ms: int
    error: str | None = None


@dataclass
class SyncResult:
    """Result of syncing to warehouse."""

    integration_id: str
    table: str
    rows_sent: int
    success: bool
    error: str | None = None


@dataclass
class InboundWebhookResult:
    """Result of processing an inbound webhook."""

    success: bool
    message: str
    data: dict | None = None


# ── Integration Service ────────────────────────────────────────────────


class IntegrationService:
    """Service for managing and dispatching integration events."""

    # Maximum consecutive failures before auto-disable
    MAX_FAILURES_BEFORE_DISABLE = 5

    # Batch size for analytics events
    ANALYTICS_BATCH_SIZE = 100

    # Flush interval for analytics batches (seconds)
    ANALYTICS_FLUSH_INTERVAL = 5

    # Retry settings for warehouse sync
    WAREHOUSE_MAX_RETRIES = 3
    WAREHOUSE_RETRY_DELAY = 1.0  # seconds, exponential backoff

    # Analytics batch storage (in-memory for demo, should be Redis in prod)
    _analytics_batches: dict[str, list[dict]] = {}
    _last_flush: dict[str, float] = {}

    def __init__(self):
        self._http_client = None

    async def get_http_client(self):
        """Get async HTTP client (lazy initialization)."""
        if self._http_client is None:
            import httpx

            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    # ── Event Dispatcher ────────────────────────────────────────

    async def dispatch_event(
        self, event_type: str, payload: dict, workspace_id: str, db: AsyncSession
    ) -> list[WebhookDispatchResult]:
        """Dispatch event to all enabled integrations subscribed to it.

        Fires each integration handler in background tasks for parallel execution.
        Logs all results regardless of success/failure.

        Args:
            event_type: Type of event to dispatch
            payload: Event payload data
            workspace_id: Workspace ID to find integrations for
            db: Database session

        Returns:
            List of dispatch results for each integration
        """
        from sqlalchemy import func

        # Find all enabled integrations subscribed to this event
        query = select(Integration).where(
            and_(
                Integration.workspace_id == workspace_id,
                Integration.enabled == True,
                # JSON contains check for events array
                func.json_array_length(Integration.events) > 0,
            )
        )

        result = await db.execute(query)
        integrations = result.scalars().all()

        # Filter by event subscription
        subscribed_integrations = [
            i for i in integrations if i.subscribes_to(event_type)
        ]

        if not subscribed_integrations:
            logger.debug(
                "No integrations subscribed to event", event_type=event_type
            )
            return []

        logger.info(
            "Dispatching event %s to %d integrations",
            event_type,
            len(subscribed_integrations),
        )

        # Dispatch to all integrations in parallel
        tasks = [
            self._dispatch_to_integration(integration, event_type, payload, db)
            for integration in subscribed_integrations
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and auto-disable failing integrations
        processed_results: list[WebhookDispatchResult] = []
        for integration, result in zip(subscribed_integrations, results):
            if isinstance(result, Exception):
                logger.warning(
                    "Integration dispatch failed",
                    integration_id=str(integration.id),
                    error=str(result),
                )
                # Log failure
                await self._log_webhook(
                    db,
                    integration.id,
                    event_type,
                    payload,
                    0,
                    str(result),
                    0,
                )
                # Increment failure and check if should disable
                if integration.increment_failure():
                    await self._disable_integration(integration, db)
                continue

            processed_results.append(result)

            # Log result
            await self._log_webhook(
                db,
                integration.id,
                event_type,
                payload,
                result.status_code or 0,
                result.error or "",
                result.duration_ms,
            )

            # Reset failure count on success
            if result.success:
                integration.reset_failure_count()

        await db.commit()
        return processed_results

    async def _dispatch_to_integration(
        self, integration: Integration, event_type: str, payload: dict, db: AsyncSession
    ) -> WebhookDispatchResult:
        """Dispatch event to a single integration based on its type."""
        start_time = time.monotonic()

        try:
            if integration.integration_type == IntegrationType.SLACK:
                await self._send_slack_alert(integration.config, event_type, payload)
                return WebhookDispatchResult(
                    integration_id=str(integration.id),
                    event_type=event_type,
                    success=True,
                    status_code=200,
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                )

            elif integration.integration_type == IntegrationType.JIRA:
                issue_url = await self._create_jira_issue(
                    integration.config, payload
                )
                return WebhookDispatchResult(
                    integration_id=str(integration.id),
                    event_type=event_type,
                    success=True,
                    status_code=200,
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                )

            elif integration.integration_type == IntegrationType.WEBHOOK:
                await self._send_generic_webhook(integration.config, payload)
                return WebhookDispatchResult(
                    integration_id=str(integration.id),
                    event_type=event_type,
                    success=True,
                    status_code=200,
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                )

            elif integration.integration_type in (
                IntegrationType.AMPLITUDE,
                IntegrationType.POSTHOG,
            ):
                await self._queue_analytics_event(
                    integration, event_type, payload
                )
                return WebhookDispatchResult(
                    integration_id=str(integration.id),
                    event_type=event_type,
                    success=True,
                    status_code=202,  # Accepted (queued)
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                )

            elif integration.integration_type == IntegrationType.SNOWFLAKE:
                await self._sync_to_warehouse(integration, payload, "snowflake")
                return WebhookDispatchResult(
                    integration_id=str(integration.id),
                    event_type=event_type,
                    success=True,
                    status_code=200,
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                )

            elif integration.integration_type == IntegrationType.BIGQUERY:
                await self._sync_to_warehouse(integration, payload, "bigquery")
                return WebhookDispatchResult(
                    integration_id=str(integration.id),
                    event_type=event_type,
                    success=True,
                    status_code=200,
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                )

            else:
                return WebhookDispatchResult(
                    integration_id=str(integration.id),
                    event_type=event_type,
                    success=False,
                    status_code=501,
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                    error=f"Unsupported integration type: {integration.integration_type}",
                )

        except Exception as e:
            logger.exception(
                "Integration dispatch error",
                integration_id=str(integration.id),
                event_type=event_type,
            )
            return WebhookDispatchResult(
                integration_id=str(integration.id),
                event_type=event_type,
                success=False,
                status_code=0,
                duration_ms=int((time.monotonic() - start_time) * 1000),
                error=str(e),
            )

    # ── Slack Integration ─────────────────────────────────────

    async def _send_slack_alert(
        self, config: dict, event_type: str, payload: dict
    ) -> None:
        """Send alert to Slack using Block Kit formatting.

        Emotion frustration spike: red alert block with session count + affected page.
        Experiment winner: green success block with variant name + conversion lift %.
        """
        client = await self.get_http_client()
        webhook_url = config.get("webhook_url")

        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return

        # Build message based on event type
        blocks = self._build_slack_blocks(event_type, payload)

        slack_payload = {"blocks": blocks}

        response = await client.post(
            webhook_url,
            json=slack_payload,
            headers={"Content-Type": "application/json"},
        )

        response.raise_for_status()
        logger.info("Slack alert sent", event_type=event_type)

    def _build_slack_blocks(self, event_type: str, payload: dict) -> list[dict]:
        """Build Slack Block Kit blocks for different event types."""
        blocks = []

        if event_type == EventType.EMOTION_FRUSTRATION_SPIKE:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 Frustration Spike Detected",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Severity:*\n{payload.get('severity', 'High')}"
                            ),
                        },
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Affected Sessions:*\n{payload.get('session_count', 0)}"
                            ),
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Page:*\n{payload.get('page_url', 'N/A')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Time:*\n{payload.get('timestamp', datetime.now(UTC).isoformat())}"
                            ),
                        },
                    ],
                },
            ]

        elif event_type == EventType.EXPERIMENT_WINNER:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🎉 Experiment Winner Declared!",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Experiment:*\n{payload.get('experiment_name', 'N/A')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Winning Variant:*\n{payload.get('winning_variant', 'N/A')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Conversion Lift:*\n{payload.get('conversion_lift', 0):.1f}%"
                            ),
                        },
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Confidence:*\n{payload.get('confidence', 0):.1f}%"
                            ),
                        },
                    ],
                },
            ]

        else:
            # Generic event
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 {event_type}",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```json\n{json.dumps(payload, indent=2)[:500]}\n```",
                    },
                },
            ]

        return blocks

    # ── Jira Integration ──────────────────────────────────────

    async def _create_jira_issue(
        self, config: dict, payload: dict
    ) -> str:
        """Create issue in Jira via REST API v3.

        Creates issue in project specified by config['project_key'].
        Type is Task, title is auto-generated from event payload.
        Returns issue URL.
        """
        client = await self.get_http_client()

        base_url = config.get("base_url", "").rstrip("/")
        email = config.get("email")
        api_token = config.get("api_token")
        project_key = config.get("project_key")

        if not all([base_url, email, api_token, project_key]):
            logger.warning("Jira configuration incomplete")
            raise ValueError("Incomplete Jira configuration")

        # Build Jira API URL
        issue_url = f"{base_url}/rest/api/3/issue"

        # Generate issue title and description from payload
        event_type = payload.get("event_type", "EmoraTest Alert")
        title = self._generate_jira_title(event_type, payload)
        description = self._generate_jira_description(payload)

        # Build Jira issue payload
        jira_payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": title,
                "description": description,
                "issuetype": {"name": "Task"},
                "priority": {
                    "name": self._get_jira_priority(event_type),
                },
            }
        }

        # Send request with Basic Auth
        auth = (email, api_token)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = await client.post(issue_url, json=jira_payload, auth=auth, headers=headers)
        response.raise_for_status()

        issue_data = response.json()
        issue_key = issue_data.get("key", "")
        issue_url = f"{base_url}/browse/{issue_key}"

        logger.info("Jira issue created", issue_key=issue_key, url=issue_url)
        return issue_url

    def _generate_jira_title(self, event_type: str, payload: dict) -> str:
        """Generate Jira issue title from event."""
        if event_type == EventType.EMOTION_FRUSTRATION_SPIKE:
            return f"[EmoraTest] Frustration Spike on {payload.get('page_url', 'Unknown')}"
        elif event_type == EventType.EXPERIMENT_WINNER:
            return f"[EmoraTest] Experiment Winner: {payload.get('experiment_name', 'Unknown')}"
        elif event_type == EventType.ANOMALY_DETECTED:
            return f"[EmoraTest] Anomaly Detected: {payload.get('anomaly_type', 'Unknown')}"
        else:
            return f"[EmoraTest] {event_type}"

    def _generate_jira_description(self, payload: dict) -> str:
        """Generate Jira issue description from payload."""
        desc = f"""h3. Event Details
Event Type: {payload.get('event_type', 'Unknown')}
Timestamp: {payload.get('timestamp', datetime.now(UTC).isoformat())}

h3. Payload Details
{json.dumps(payload, indent=2)}

h3. Recommended Action
{payload.get('recommended_action', 'Investigate manually')}
"""
        return desc

    def _get_jira_priority(self, event_type: str) -> str:
        """Get Jira priority based on event type."""
        if event_type == EventType.EMOTION_FRUSTRATION_SPIKE:
            return "High"
        elif event_type == EventType.ANOMALY_DETECTED:
            return "Medium"
        elif event_type == EventType.EXPERIMENT_WINNER:
            return "Low"
        else:
            return "Medium"

    # ── Analytics Integrations ───────────────────────────────

    async def _queue_analytics_event(
        self, integration: Integration, event_type: str, payload: dict
    ) -> None:
        """Queue event for batch sending to Amplitude or PostHog.

        Batches up to ANALYTICS_BATCH_SIZE events before sending.
        Flushes every ANALYTICS_FLUSH_INTERVAL seconds.
        """
        integration_id = str(integration.id)

        # Initialize batch for this integration
        if integration_id not in self._analytics_batches:
            self._analytics_batches[integration_id] = []

        # Add event to batch
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            **payload,
        }
        self._analytics_batches[integration_id].append(event)

        # Check if should flush
        batch_size = len(self._analytics_batches[integration_id])
        should_flush = (
            batch_size >= self.ANALYTICS_BATCH_SIZE
            or self._should_flush_analytics_batch(integration_id)
        )

        if should_flush:
            await self._flush_analytics_batch(integration)

    def _should_flush_analytics_batch(self, integration_id: str) -> bool:
        """Check if analytics batch should flush based on time."""
        last_flush = self._last_flush.get(integration_id, 0.0)
        return (time.time() - last_flush) >= self.ANALYTICS_FLUSH_INTERVAL

    async def _flush_analytics_batch(self, integration_id: str) -> None:
        """Flush queued analytics events to the integration."""
        if integration_id not in self._analytics_batches:
            return

        batch = self._analytics_batches[integration_id]
        if not batch:
            return

        logger.info("Flushing analytics batch", integration_id=integration_id, size=len(batch))

        # Send batch (implementation depends on integration type)
        # For now, just log - actual API calls would be here
        logger.debug("Analytics batch events", events=batch)

        # Clear batch and update last flush time
        self._analytics_batches[integration_id] = []
        self._last_flush[integration_id] = time.time()

    async def sync_experiment_exposure(
        self,
        integration_id: str,
        user_id: str,
        experiment_id: str,
        variant_id: str,
    ) -> None:
        """Send experiment exposure event to Amplitude or PostHog.

        Sends $experiment_started event with variant as property.
        """
        event = {
            "event_type": "$experiment_started",
            "user_id": user_id,
            "event_properties": {
                "experiment_id": experiment_id,
                "variant_id": variant_id,
            },
            "time": int(time.time() * 1000),
        }

        logger.info(
            "Experiment exposure synced",
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
        )

        # In production, would add to batch for the specific integration

    # ── Data Warehouse Integrations ───────────────────────────

    async def _sync_to_warehouse(
        self, integration: Integration, payload: dict, warehouse_type: str
    ) -> None:
        """Sync data to Snowflake or BigQuery.

        Snowflake: use snowflake-connector-python, write to schema.table
        BigQuery: use google-cloud-bigquery, streaming insert
        Schema auto-detection from first row.
        Retry up to WAREHOUSE_MAX_RETRIES times with exponential backoff.
        """
        rows = payload.get("rows", [])
        table = payload.get("table", "events")

        if not rows or not table:
            logger.warning("No rows or table specified for warehouse sync")
            return

        config = integration.config
        last_error = None

        for attempt in range(self.WAREHOUSE_MAX_RETRIES):
            try:
                if warehouse_type == "snowflake":
                    await self._sync_to_snowflake(config, table, rows)
                elif warehouse_type == "bigquery":
                    await self._sync_to_bigquery(config, table, rows)

                logger.info(
                    "Warehouse sync succeeded",
                    warehouse_type=warehouse_type,
                    table=table,
                    rows=len(rows),
                    attempt=attempt + 1,
                )
                return

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "Warehouse sync attempt failed",
                    warehouse_type=warehouse_type,
                    attempt=attempt + 1,
                    error=last_error,
                )
                if attempt < self.WAREHOUSE_MAX_RETRIES - 1:
                    await asyncio.sleep(
                        self.WAREHOUSE_RETRY_DELAY * (2**attempt)
                    )

        logger.error(
            "Warehouse sync failed after all retries",
            warehouse_type=warehouse_type,
            error=last_error,
        )
        raise Exception(f"Warehouse sync failed: {last_error}")

    async def _sync_to_snowflake(
        self, config: dict, table: str, rows: list[dict]
    ) -> None:
        """Sync rows to Snowflake data warehouse.

        TODO: Implement with snowflake-connector-python
        For now, this is a stub that logs the intent.
        """
        account = config.get("account")
        user = config.get("user")
        password = config.get("password")
        database = config.get("database")
        schema = config.get("schema", "public")

        logger.info(
            "Snowflake sync (stub)",
            table=table,
            schema=schema,
            rows=len(rows),
        )

        # In production:
        # import snowflake.connector
        # conn = snowflake.connector.connect(
        #     account=account, user=user, password=password, database=database
        # )
        # cursor = conn.cursor()
        # cursor.execute(f"INSERT INTO {schema}.{table} ...")
        # conn.commit()

    async def _sync_to_bigquery(
        self, config: dict, table: str, rows: list[dict]
    ) -> None:
        """Sync rows to Google BigQuery via streaming insert.

        TODO: Implement with google-cloud-bigquery
        For now, this is a stub that logs the intent.
        """
        project_id = config.get("project_id")
        dataset_id = config.get("dataset_id")
        credentials = config.get("credentials_json")

        logger.info(
            "BigQuery sync (stub)",
            table=table,
            dataset=dataset_id,
            project=project_id,
            rows=len(rows),
        )

        # In production:
        # from google.cloud import bigquery
        # client = bigquery.Client.from_service_account_json(credentials)
        # table_ref = f"{project_id}.{dataset_id}.{table}"
        # errors = client.insert_rows_json(table_ref, rows)
        # if errors:
        #     raise Exception(f"BigQuery insert errors: {errors}")

    # ── Generic Webhook ────────────────────────────────────

    async def _send_generic_webhook(
        self, config: dict, payload: dict
    ) -> None:
        """Send payload to a generic webhook URL."""
        client = await self.get_http_client()
        webhook_url = config.get("webhook_url")

        if not webhook_url:
            logger.warning("Webhook URL not configured")
            return

        headers = config.get("headers", {})
        headers["Content-Type"] = "application/json"

        response = await client.post(
            webhook_url,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()

        logger.info("Generic webhook sent", webhook_url=webhook_url)

    # ── Inbound Webhooks ─────────────────────────────────────

    def verify_signature(
        self, payload: bytes, signature: str, secret: str
    ) -> bool:
        """Verify HMAC-SHA256 signature for inbound webhooks.

        Args:
            payload: Raw request body bytes
            signature: Signature from request header
            secret: Shared secret for verification

        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)

    async def handle_inbound(
        self, integration_type: str, payload: dict, db: AsyncSession
    ) -> InboundWebhookResult:
        """Handle an inbound webhook from a third-party service.

        Processes the payload based on integration type.

        Args:
            integration_type: Type of integration (amplitude, posthog, etc.)
            payload: Webhook payload data
            db: Database session

        Returns:
            InboundWebhookResult with processing status
        """
        try:
            if integration_type == "amplitude":
                return await self._handle_amplitude_webhook(payload, db)
            elif integration_type == "posthog":
                return await self._handle_posthog_webhook(payload, db)
            elif integration_type == "zapier":
                return await self._handle_zapier_webhook(payload, db)
            else:
                return InboundWebhookResult(
                    success=False,
                    message=f"Unsupported inbound webhook type: {integration_type}",
                )

        except Exception as e:
            logger.exception("Inbound webhook processing error", integration_type=integration_type)
            return InboundWebhookResult(
                success=False, message=f"Processing error: {str(e)}"
            )

    async def _handle_amplitude_webhook(
        self, payload: dict, db: AsyncSession
    ) -> InboundWebhookResult:
        """Handle inbound Amplitude webhook (e.g., cohort updates)."""
        logger.info("Amplitude webhook received", event_type=payload.get("event_type"))
        return InboundWebhookResult(
            success=True,
            message="Amplitude webhook processed",
            data=payload,
        )

    async def _handle_posthog_webhook(
        self, payload: dict, db: AsyncSession
    ) -> InboundWebhookResult:
        """Handle inbound PostHog webhook (e.g., feature flag updates)."""
        logger.info("PostHog webhook received", event_type=payload.get("event_type"))
        return InboundWebhookResult(
            success=True,
            message="PostHog webhook processed",
            data=payload,
        )

    async def _handle_zapier_webhook(
        self, payload: dict, db: AsyncSession
    ) -> InboundWebhookResult:
        """Handle Zapier poll request for experiment data.

        Returns experiment data for Zapier to process.
        """
        # In production, would query experiments and return data
        logger.info("Zapier poll received")
        return InboundWebhookResult(
            success=True,
            message="Zapier webhook processed",
            data={"experiments": []},  # Placeholder
        )

    # ── Helper Methods ─────────────────────────────────────

    async def _log_webhook(
        self,
        db: AsyncSession,
        integration_id: uuid.UUID,
        event_type: str,
        payload: dict,
        status_code: int,
        error: str,
        duration_ms: int,
    ) -> None:
        """Log webhook dispatch result."""

        log_entry = WebhookLog(
            integration_id=integration_id,
            event_type=event_type,
            payload=payload,
            response_status=status_code,
            response_body=error,
            duration_ms=duration_ms,
        )

        db.add(log_entry)
        # Commit happens in calling function

    async def _disable_integration(
        self, integration: Integration, db: AsyncSession
    ) -> None:
        """Auto-disable a failing integration and alert workspace owner."""
        integration.enabled = False
        integration.updated_at = datetime.now(UTC)

        # TODO: Send email alert to workspace owner
        logger.warning(
            "Integration auto-disabled due to failures",
            integration_id=str(integration.id),
            name=integration.name,
        )


# ── Singleton instance ──────────────────────────────────────────

_service_instance: IntegrationService | None = None


def get_integration_service() -> IntegrationService:
    """Get singleton instance of IntegrationService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = IntegrationService()
    return _service_instance


# ── Helper Methods Added to Service ──────────────────────────────────────


# Add these helper methods to IntegrationService class above
def _validate_integration_config(integration_type: str, config: dict) -> None:
    """Validate integration config based on type."""
    from app.models.integration import IntegrationType

    if integration_type == IntegrationType.SLACK:
        if not config.get("webhook_url"):
            raise ValueError("Slack integration requires webhook_url")

    elif integration_type == IntegrationType.JIRA:
        required = ["base_url", "email", "api_token", "project_key"]
        missing = [k for k in required if not config.get(k)]
        if missing:
            raise ValueError(f"Jira integration requires: {', '.join(missing)}")

    elif integration_type == IntegrationType.AMPLITUDE:
        if not config.get("api_key"):
            raise ValueError("Amplitude integration requires api_key")

    elif integration_type == IntegrationType.POSTHOG:
        if not config.get("api_key") or not config.get("project_id"):
            raise ValueError("PostHog integration requires api_key and project_id")

    elif integration_type == IntegrationType.SNOWFLAKE:
        required = ["account", "user", "password", "database", "schema"]
        missing = [k for k in required if not config.get(k)]
        if missing:
            raise ValueError(f"Snowflake integration requires: {', '.join(missing)}")

    elif integration_type == IntegrationType.BIGQUERY:
        required = ["project_id", "dataset_id", "credentials_json"]
        missing = [k for k in required if not config.get(k)]
        if missing:
            raise ValueError(f"BigQuery integration requires: {', '.join(missing)}")

    elif integration_type == IntegrationType.WEBHOOK:
        if not config.get("webhook_url"):
            raise ValueError("Webhook integration requires webhook_url")


def _get_default_events(integration_type: str) -> list[str]:
    """Get default events for an integration type."""
    from app.models.integration import EventType

    defaults = {
        "slack": [
            EventType.EXPERIMENT_WINNER,
            EventType.EMOTION_FRUSTRATION_SPIKE,
            EventType.ANOMALY_DETECTED,
        ],
        "jira": [
            EventType.EMOTION_FRUSTRATION_SPIKE,
            EventType.ANOMALY_DETECTED,
            EventType.EXPERIMENT_STOPPED,
        ],
        "amplitude": [
            EventType.EXPERIMENT_STARTED,
            EventType.EXPERIMENT_WINNER,
            EventType.SESSION_ENDED,
        ],
        "posthog": [
            EventType.EXPERIMENT_STARTED,
            EventType.EXPERIMENT_WINNER,
            EventType.SESSION_ENDED,
        ],
        "snowflake": [
            EventType.SESSION_ENDED,
            EventType.EXPERIMENT_WINNER,
        ],
        "bigquery": [
            EventType.SESSION_ENDED,
            EventType.EXPERIMENT_WINNER,
        ],
        "webhook": [],
        "zapier": [],
    }

    return defaults.get(integration_type, [])


# Monkey-patch the methods into IntegrationService
IntegrationService._validate_integration_config = staticmethod(_validate_integration_config)
IntegrationService._get_default_events = staticmethod(_get_default_events)
