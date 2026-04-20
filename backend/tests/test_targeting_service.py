"""Tests for TargetingService and segment evaluation."""

import pytest

from app.models.segment import (
    Segment,
)
from app.services.targeting_service import (
    TargetingService,
)


@pytest.fixture
def service():
    """Create a TargetingService instance."""
    return TargetingService()


@pytest.fixture
def sample_user_context():
    """Sample user context for testing."""
    return {
        "user_id": "user_123",
        "user": {
            "country": "US",
            "city": "New York",
            "device_type": "desktop",
            "browser": "Chrome",
            "plan": "premium",
            "ltv": 1500,
        },
        "session": {
            "emotion": "frustration",
            "frustration_score": 0.8,
            "churn_risk": 0.7,
        },
        "event": {
            "page_url": "/checkout",
            "referrer": "google.com",
            "utm_source": "newsletter",
            "utm_campaign": "spring_sale",
        },
    }


# ── Condition Evaluation Tests ────────────────────────────────────────


class TestConditionEvaluation:
    """Tests for evaluating individual conditions."""

    def test_evaluate_eq_condition(self, service, sample_user_context):
        """Test equality operator."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [{"attribute": "user.country", "operator": "eq", "value": "US"}],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is True

    def test_evaluate_neq_condition(self, service, sample_user_context):
        """Test not equal operator."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {"attribute": "user.country", "operator": "neq", "value": "UK"}
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is True

    def test_evaluate_gt_condition(self, service, sample_user_context):
        """Test greater than operator."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {"attribute": "user.ltv", "operator": "gt", "value": 1000}
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is True

    def test_evaluate_lt_condition(self, service, sample_user_context):
        """Test less than operator."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {"attribute": "session.frustration_score", "operator": "lt", "value": 1.0}
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is True

    def test_evaluate_contains_condition(self, service, sample_user_context):
        """Test contains operator."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {"attribute": "event.page_url", "operator": "contains", "value": "checkout"}
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is True

    def test_evaluate_in_condition(self, service, sample_user_context):
        """Test in operator."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {
                        "attribute": "user.device_type",
                        "operator": "in",
                        "value": ["desktop", "tablet"],
                    }
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is True

    def test_evaluate_not_in_condition(self, service, sample_user_context):
        """Test not_in operator."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {"attribute": "user.device_type", "operator": "not_in", "value": ["mobile"]}
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is True

    def test_evaluate_regex_condition(self, service, sample_user_context):
        """Test regex operator."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {
                        "attribute": "user.city",
                        "operator": "regex",
                        "value": r"^New",
                    }
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is True


# ── Condition Group Tests ────────────────────────────────────────────


class TestConditionGroups:
    """Tests for nested condition groups."""

    def test_and_operator_all_must_match(self, service, sample_user_context):
        """Test AND requires all conditions to match."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {"attribute": "user.country", "operator": "eq", "value": "US"},
                    {"attribute": "user.plan", "operator": "eq", "value": "premium"},
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is True

    def test_and_operator_one_fails(self, service, sample_user_context):
        """Test AND fails when one condition doesn't match."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {"attribute": "user.country", "operator": "eq", "value": "US"},
                    {"attribute": "user.plan", "operator": "eq", "value": "free"},
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is False

    def test_or_operator_one_matches(self, service, sample_user_context):
        """Test OR passes when one condition matches."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "OR",
                "conditions": [
                    {"attribute": "user.plan", "operator": "eq", "value": "free"},
                    {"attribute": "user.plan", "operator": "eq", "value": "premium"},
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is True

    def test_or_operator_none_match(self, service, sample_user_context):
        """Test OR fails when no conditions match."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "OR",
                "conditions": [
                    {"attribute": "user.plan", "operator": "eq", "value": "free"},
                    {"attribute": "user.plan", "operator": "eq", "value": "basic"},
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is False

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_nested_conditions(self, service, sample_user_context):
        """Test nested AND/OR groups."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {
                        "operator": "OR",
                        "conditions": [
                            {"attribute": "user.country", "operator": "eq", "value": "US"},
                            {"attribute": "user.country", "operator": "eq", "value": "UK"},
                        ],
                    },
                    {"attribute": "user.plan", "operator": "eq", "value": "premium"},
                ],
            },
            segment_type="static",
        )
        assert service.evaluate_segment(segment, sample_user_context) is True


# ── Variant Assignment Tests ───────────────────────────────────────


class TestVariantAssignment:
    """Tests for experiment variant assignment."""

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_assign_with_targeting_match(self, service, sample_user_context):
        """Test assignment when user matches targeting rules."""
        experiment = {
            "id": "exp_123",
            "targeting_rules": {
                "operator": "AND",
                "conditions": [
                    {"attribute": "user.country", "operator": "eq", "value": "US"}
                ],
            },
            "variants": [
                {"id": "control", "weight": 1.0},
                {"id": "variant_a", "weight": 1.0},
            ],
        }

        result = service.assign_experiment_variant(experiment, sample_user_context)

        assert result.variant_id in ["control", "variant_a"]
        assert "deterministic hash" in result.assignment_reason

    def test_assign_with_targeting_exclude(self, service, sample_user_context):
        """Test assignment when user is excluded by targeting."""
        experiment = {
            "id": "exp_123",
            "targeting_rules": {
                "operator": "AND",
                "conditions": [
                    {"attribute": "user.country", "operator": "eq", "value": "UK"}
                ],
            },
            "variants": [{"id": "control", "weight": 1.0}],
        }

        result = service.assign_experiment_variant(experiment, sample_user_context)

        assert result.variant_id is None
        assert "excluded by targeting rules" in result.assignment_reason

    def test_deterministic_assignment(self, service, sample_user_context):
        """Test that assignment is deterministic for same user."""
        experiment = {
            "id": "exp_123",
            "variants": [
                {"id": "control", "weight": 1.0},
                {"id": "variant_a", "weight": 1.0},
            ],
        }

        # Assign twice for same user
        result1 = service.assign_experiment_variant(experiment, sample_user_context)
        result2 = service.assign_experiment_variant(experiment, sample_user_context)

        # Should get same variant
        assert result1.variant_id == result2.variant_id
        assert result1.bucket_value == result2.bucket_value


# ── Helper Method Tests ────────────────────────────────────────────


class TestHelperMethods:
    """Tests for helper methods."""

    def test_get_referenced_attributes(self, service):
        """Test extracting attribute references from conditions."""
        segment = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {"attribute": "user.country", "operator": "eq", "value": "US"},
                    {"attribute": "user.plan", "operator": "eq", "value": "premium"},
                    {
                        "operator": "OR",
                        "conditions": [
                            {"attribute": "session.emotion", "operator": "eq", "value": "frustration"},
                            {"attribute": "session.emotion", "operator": "eq", "value": "confusion"},
                        ],
                    },
                ],
            },
            segment_type="static",
        )

        attrs = segment.get_referenced_attributes()

        assert "session.emotion" in attrs
        assert "user.country" in attrs
        assert "user.plan" in attrs

    def test_get_condition_depth(self, service):
        """Test calculating condition tree depth."""
        # Simple condition
        segment1 = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {"attribute": "user.country", "operator": "eq", "value": "US"}
                ],
            },
            segment_type="static",
        )
        assert segment1.get_condition_depth() == 1

        # Nested conditions
        segment2 = Segment(
            merchant_id=None,  # type: ignore
            name="test",
            conditions={
                "operator": "AND",
                "conditions": [
                    {
                        "operator": "OR",
                        "conditions": [
                            {"attribute": "user.country", "operator": "eq", "value": "US"},
                            {
                                "operator": "OR",
                                "conditions": [
                                    {"attribute": "user.country", "operator": "eq", "value": "UK"}
                                ],
                            },
                        ],
                    }
                ],
            },
            segment_type="static",
        )
        assert segment2.get_condition_depth() == 3


# ── Hash to Bucket Tests ─────────────────────────────────────────────


class TestHashToBucket:
    """Tests for deterministic hashing."""

    def test_hash_consistency(self, service):
        """Test that same key produces same bucket value."""
        key = "experiment:user123"
        value1 = service._hash_to_bucket(key)
        value2 = service._hash_to_bucket(key)

        assert value1 == value2
        assert 0.0 <= value1 <= 1.0

    def test_hash_distribution(self, service):
        """Test that hash values are distributed across range."""
        keys = [f"key_{i}" for i in range(1000)]
        values = [service._hash_to_bucket(k) for k in keys]

        # Check values are in valid range
        assert all(0.0 <= v <= 1.0 for v in values)

        # Check distribution (should be roughly uniform)
        buckets = [0] * 10
        for v in values:
            buckets[int(v * 10)] += 1

        # Each bucket should have roughly 10% of values
        # Allow for some variance but not extreme
        assert all(50 <= count <= 150 for count in buckets)
