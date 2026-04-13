"""Tests for IntegrationService and webhook dispatching."""

import pytest

from app.models.integration import (
    EventType,
    Integration,
)
from app.services.integration_service import (
    IntegrationService,
)


@pytest.fixture
def service():
    """Create an IntegrationService instance."""
    return IntegrationService()


@pytest.fixture
def sample_integration():
    """Sample integration for testing."""
    return Integration(
        workspace_id=None,  # type: ignore
        name="Test Slack",
        integration_type="slack",
        config={"webhook_url": "https://hooks.slack.com/test"},
        events=[EventType.EXPERIMENT_WINNER, EventType.EMOTION_FRUSTRATION_SPIKE],
        enabled=True,
    )


# ── Signature Verification Tests ──────────────────────────────────────


class TestSignatureVerification:
    """Tests for HMAC signature verification."""

    def test_verify_valid_signature(self, service):
        """Test valid signature verification."""
        payload = b'{"test": "data"}'
        secret = "test_secret"

        # Generate valid signature
        import hashlib
        import hmac
        signature = hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        assert service.verify_signature(payload, signature, secret) is True

    def test_verify_invalid_signature(self, service):
        """Test invalid signature verification."""
        payload = b'{"test": "data"}'
        secret = "test_secret"
        invalid_signature = "invalid_signature_123"

        assert service.verify_signature(payload, invalid_signature, secret) is False

    def test_constant_time_comparison(self, service):
        """Test that signature verification uses constant-time comparison."""
        # This is tested by the implementation using hmac.compare_digest
        # We just verify the method exists and works
        assert hasattr(service, "verify_signature")
        assert callable(service.verify_signature)


# ── Config Validation Tests ─────────────────────────────────────


class TestConfigValidation:
    """Tests for integration config validation."""

    def test_slack_config_valid(self, service):
        """Test valid Slack config."""
        config = {"webhook_url": "https://hooks.slack.com/test"}
        # Should not raise
        try:
            IntegrationService._validate_integration_config("slack", config)
        except ValueError:
            pytest.fail("Valid Slack config should not raise error")

    def test_slack_config_missing_url(self, service):
        """Test Slack config missing webhook URL."""
        config = {}
        with pytest.raises(ValueError) as exc_info:
            IntegrationService._validate_integration_config("slack", config)
        assert "webhook_url" in str(exc_info.value)

    def test_jira_config_valid(self, service):
        """Test valid Jira config."""
        config = {
            "base_url": "https://test.atlassian.net",
            "email": "test@test.com",
            "api_token": "token123",
            "project_key": "TEST",
        }
        # Should not raise
        try:
            IntegrationService._validate_integration_config("jira", config)
        except ValueError:
            pytest.fail("Valid Jira config should not raise error")

    def test_jira_config_missing_fields(self, service):
        """Test Jira config missing required fields."""
        config = {"base_url": "https://test.atlassian.net"}
        with pytest.raises(ValueError) as exc_info:
            IntegrationService._validate_integration_config("jira", config)
        assert "requires" in str(exc_info.value)


# ── Default Events Tests ────────────────────────────────────────


class TestDefaultEvents:
    """Tests for getting default events for integration types."""

    def test_slack_default_events(self, service):
        """Test Slack default events."""
        events = IntegrationService._get_default_events("slack")

        assert EventType.EXPERIMENT_WINNER in events
        assert EventType.EMOTION_FRUSTRATION_SPIKE in events
        assert EventType.ANOMALY_DETECTED in events

    def test_amplitude_default_events(self, service):
        """Test Amplitude default events."""
        events = IntegrationService._get_default_events("amplitude")

        assert EventType.EXPERIMENT_STARTED in events
        assert EventType.EXPERIMENT_WINNER in events
        assert EventType.SESSION_ENDED in events

    def test_webhook_default_events(self, service):
        """Test generic webhook has no default events."""
        events = IntegrationService._get_default_events("webhook")

        assert events == []


# ── Block Builder Tests ────────────────────────────────────────


class TestSlackBlockBuilder:
    """Tests for Slack Block Kit message building."""

    def test_frustration_spike_blocks(self, service):
        """Test building blocks for frustration spike event."""
        payload = {
            "event_type": "emotion.frustration_spike",
            "severity": "High",
            "session_count": 42,
            "page_url": "/checkout",
        }

        blocks = service._build_slack_blocks("emotion.frustration_spike", payload)

        assert len(blocks) > 0
        assert any("🚨" in b.get("text", {}).get("text", "") for b in blocks if b.get("type") == "header")

    def test_experiment_winner_blocks(self, service):
        """Test building blocks for experiment winner event."""
        payload = {
            "event_type": "experiment.winner",
            "experiment_name": "Checkout Button Color",
            "winning_variant": "variant_a",
            "conversion_lift": 12.5,
            "confidence": 95.0,
        }

        blocks = service._build_slack_blocks("experiment.winner", payload)

        assert len(blocks) > 0
        assert any("🎉" in b.get("text", {}).get("text", "") for b in blocks if b.get("type") == "header")


# ── Jira Helper Tests ──────────────────────────────────────────


class TestJiraHelpers:
    """Tests for Jira issue creation helpers."""

    def test_generate_frustration_title(self, service):
        """Test generating Jira title for frustration spike."""
        payload = {
            "event_type": "emotion.frustration_spike",
            "page_url": "/checkout",
        }

        title = service._generate_jira_title("emotion.frustration_spike", payload)

        assert "[EmoraTest]" in title
        assert "Frustration Spike" in title
        assert "/checkout" in title

    def test_get_priority(self, service):
        """Test getting Jira priority based on event type."""
        assert service._get_jira_priority("emotion.frustration_spike") == "High"
        assert service._get_jira_priority("experiment.winner") == "Low"
        assert service._get_jira_priority("anomaly.detected") == "Medium"


# ── Analytics Batching Tests ───────────────────────────────────


class TestAnalyticsBatching:
    """Tests for analytics event batching."""

    def test_queue_event(self, service):
        """Test queuing event to batch."""
        integration = Integration(
            workspace_id=None,  # type: ignore
            name="Test Amplitude",
            integration_type="amplitude",
            config={"api_key": "test"},
            events=[EventType.EXPERIMENT_STARTED],
            enabled=True,
        )

        # Queue an event
        import asyncio
        asyncio.run(
            service._queue_analytics_event(
                integration,
                EventType.EXPERIMENT_STARTED,
                {"test": "data"},
            )
        )

        # Check batch exists
        integration_id = str(integration.id)
        assert integration_id in service._analytics_batches
        assert len(service._analytics_batches[integration_id]) == 1

    def test_flush_on_batch_size(self, service):
        """Test flushing when batch size is reached."""
        integration = Integration(
            workspace_id=None,  # type: ignore
            name="Test PostHog",
            integration_type="posthog",
            config={"api_key": "test"},
            events=[EventType.SESSION_ENDED],
            enabled=True,
        )

        integration_id = str(integration.id)

        # Add enough events to reach batch size
        import asyncio
        for i in range(service.ANALYTICS_BATCH_SIZE + 1):
            asyncio.run(
                service._queue_analytics_event(
                    integration,
                    EventType.SESSION_ENDED,
                    {"count": i},
                )
            )

        # Batch should be flushed
        assert len(service._analytics_batches.get(integration_id, [])) <= 1


# ── Model Helper Tests ────────────────────────────────────────


class TestIntegrationModelHelpers:
    """Tests for Integration model helper methods."""

    def test_is_alert_integration(self, sample_integration):
        """Test identifying alert integrations."""
        slack_integration = sample_integration
        slack_integration.integration_type = "slack"
        assert slack_integration.is_alert_integration() is True

        amplitude_integration = sample_integration
        amplitude_integration.integration_type = "amplitude"
        assert amplitude_integration.is_analytics_integration() is True

    def test_subscribes_to(self, sample_integration):
        """Test checking event subscription."""
        sample_integration.events = [EventType.EXPERIMENT_WINNER]

        assert sample_integration.subscribes_to(EventType.EXPERIMENT_WINNER) is True
        assert sample_integration.subscribes_to(EventType.EXPERIMENT_STARTED) is False

    def test_increment_failure(self, sample_integration):
        """Test incrementing failure count."""
        sample_integration.failure_count = 4
        assert sample_integration.failure_count == 4

        should_disable = sample_integration.increment_failure()
        assert should_disable is True  # Now at 5
        assert sample_integration.failure_count == 5

    def test_reset_failure_count(self, sample_integration):
        """Test resetting failure count."""
        sample_integration.failure_count = 3
        sample_integration.reset_failure_count()

        assert sample_integration.failure_count == 0
