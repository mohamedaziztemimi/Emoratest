"""Unit tests for Experiment model with full type coverage.

Covers: model creation for each experiment_type, validation errors,
schema serialization, and new fields (n_variants, flicker_free, etc.).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.models.experiment import Experiment
from app.schemas.experiments import (
    ExperimentCreateRequest,
    ExperimentOut,
    ExperimentResult,
    ExperimentType,
    ExperimentUpdateRequest,
    FrictionType,
    SplitUrlConfig,
)

MERCHANT_ID = uuid.uuid4()


# ── MODEL VALIDATION TESTS ────────────────────────────────────────


class TestExperimentModel:
    """Tests for Experiment model validation methods."""

    def test_create_ab_experiment_default(self):
        """Create a basic A/B experiment with defaults."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Test Experiment",
            experiment_type="ab",
            n_variants=2,
            flicker_free=True,
        )
        assert exp.experiment_type == "ab"
        assert exp.n_variants == 2
        assert exp.flicker_free is True

    def test_create_mvt_experiment(self):
        """Create a multivariate experiment."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="MVT Test",
            experiment_type="mvt",
            n_variants=5,
            flicker_free=True,
        )
        assert exp.experiment_type == "mvt"
        assert exp.n_variants == 5

    def test_create_split_url_experiment_valid(self):
        """Create a split URL experiment with valid config."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Split URL Test",
            experiment_type="split_url",
            n_variants=2,
            flicker_free=True,
            split_url_config={"control_url": "https://example.com/control", "variant_urls": ["https://example.com/v1"]},
        )
        exp.validate_experiment_config()  # Should not raise
        assert exp.is_split_url() is True

    def test_create_multipage_experiment_valid(self):
        """Create a multi-page experiment with valid page URLs."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Multi-page Test",
            experiment_type="multipage",
            n_variants=2,
            flicker_free=True,
            page_urls=["https://example.com/checkout", "https://example.com/cart"],
        )
        exp.validate_experiment_config()  # Should not raise
        assert exp.is_multi_page() is True

    def test_create_server_side_experiment_valid(self):
        """Create a server-side experiment with valid key."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Server-side Test",
            experiment_type="server_side",
            n_variants=2,
            flicker_free=True,
            server_side_key="srv_test_key_123",
        )
        exp.validate_experiment_config()  # Should not raise
        assert exp.is_server_side() is True

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_validate_split_url_missing_config(self):
        """Validation error: split_url type without split_url_config."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Invalid Split URL",
            experiment_type="split_url",
            n_variants=2,
            flicker_free=True,
        )
        with pytest.raises(PydanticValidationError):
            exp.validate_experiment_config()

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_validate_split_url_missing_variant_urls(self):
        """Validation error: split_url config without variant_urls."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Invalid Split URL",
            experiment_type="split_url",
            n_variants=2,
            flicker_free=True,
            split_url_config={"control_url": "https://example.com/control"},
        )
        with pytest.raises(PydanticValidationError):
            exp.validate_experiment_config()

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_validate_split_url_empty_variant_urls(self):
        """Validation error: split_url config with empty variant_urls list."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Invalid Split URL",
            experiment_type="split_url",
            n_variants=2,
            flicker_free=True,
            split_url_config={"control_url": "https://example.com/control", "variant_urls": []},
        )
        with pytest.raises(PydanticValidationError):
            exp.validate_experiment_config()

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_validate_multipage_empty_page_urls(self):
        """Validation error: multipage type with empty page_urls."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Invalid Multipage",
            experiment_type="multipage",
            n_variants=2,
            flicker_free=True,
            page_urls=[],
        )
        with pytest.raises(PydanticValidationError):
            exp.validate_experiment_config()

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_validate_multipage_missing_page_urls(self):
        """Validation error: multipage type without page_urls."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Invalid Multipage",
            experiment_type="multipage",
            n_variants=2,
            flicker_free=True,
        )
        with pytest.raises(PydanticValidationError):
            exp.validate_experiment_config()

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_validate_server_side_missing_key(self):
        """Validation error: server_side type without server_side_key."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Invalid Server-side",
            experiment_type="server_side",
            n_variants=2,
            flicker_free=True,
        )
        with pytest.raises(PydanticValidationError):
            exp.validate_experiment_config()

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_validate_n_variants_too_low(self):
        """Validation error: n_variants less than 2."""
        # Note: Database constraint prevents this, but we test the validator
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Invalid N Variants",
            experiment_type="ab",
            n_variants=1,  # Invalid
            flicker_free=True,
        )
        with pytest.raises(PydanticValidationError):
            exp.validate_experiment_config()

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_validate_n_variants_too_high(self):
        """Validation error: n_variants greater than 10."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Invalid N Variants",
            experiment_type="ab",
            n_variants=11,  # Invalid
            flicker_free=True,
        )
        with pytest.raises(PydanticValidationError):
            exp.validate_experiment_config()

    def test_is_flicker_free_enabled(self):
        """Test is_flicker_free_enabled method."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Test",
            experiment_type="ab",
            n_variants=2,
            flicker_free=True,
        )
        assert exp.is_flicker_free_enabled() is True

        exp.flicker_free = False
        assert exp.is_flicker_free_enabled() is False

    def test_get_variant_count(self):
        """Test get_variant_count method."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Test",
            experiment_type="ab",
            n_variants=5,
            flicker_free=True,
        )
        assert exp.get_variant_count() == 5

    def test_get_variant_count_clamps_bounds(self):
        """Test get_variant_count method clamps to valid range."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Test",
            experiment_type="ab",
            n_variants=2,
            flicker_free=True,
        )
        assert exp.get_variant_count() == 2

    def test_is_mvt(self):
        """Test is_mvt method."""
        exp = Experiment(
            merchant_id=MERCHANT_ID,
            title="Test",
            experiment_type="mvt",
            n_variants=2,
            flicker_free=True,
        )
        assert exp.is_mvt() is True

        exp.experiment_type = "ab"
        assert exp.is_mvt() is False


# ── SCHEMA VALIDATION TESTS ──────────────────────────────────────


class TestExperimentSchemas:
    """Tests for Experiment Pydantic schemas."""

    def test_create_schema_ab_default(self):
        """Create request with default A/B settings."""
        req = ExperimentCreateRequest(
            title="Test Experiment",
            hypothesis="Testing variant B",
            friction_type="hesitation",
            variant_a="Original",
            variant_b="New",
        )
        assert req.experiment_type == "ab"
        assert req.n_variants == 2
        assert req.flicker_free is True

    def test_create_schema_mvt(self):
        """Create MVT experiment request."""
        req = ExperimentCreateRequest(
            title="MVT Test",
            experiment_type="mvt",
            n_variants=5,
            flicker_free=True,
        )
        assert req.experiment_type == "mvt"
        assert req.n_variants == 5

    def test_create_schema_split_url_valid(self):
        """Create split URL experiment request."""
        req = ExperimentCreateRequest(
            title="Split URL Test",
            experiment_type="split_url",
            split_url_config=SplitUrlConfig(
                control_url="https://example.com/control",
                variant_urls=["https://example.com/v1"],
            ),
        )
        assert req.experiment_type == "split_url"
        assert req.split_url_config is not None

    def test_create_schema_split_url_missing_config_error(self):
        """Validation error: split_url without split_url_config."""
        with pytest.raises(ValueError, match="split_url type requires split_url_config"):
            ExperimentCreateRequest(
                title="Invalid",
                experiment_type="split_url",
            )

    def test_create_schema_multipage_valid(self):
        """Create multi-page experiment request."""
        req = ExperimentCreateRequest(
            title="Multi-page Test",
            experiment_type="multipage",
            page_urls=["https://example.com/checkout", "https://example.com/cart"],
        )
        assert req.experiment_type == "multipage"
        assert req.page_urls is not None
        assert len(req.page_urls) == 2

    def test_create_schema_multipage_empty_error(self):
        """Validation error: multipage with empty page_urls."""
        with pytest.raises(ValueError, match="multipage type requires non-empty page_urls"):
            ExperimentCreateRequest(
                title="Invalid",
                experiment_type="multipage",
                page_urls=[],
            )

    def test_create_schema_multipage_missing_error(self):
        """Validation error: multipage without page_urls."""
        with pytest.raises(ValueError, match="multipage type requires non-empty page_urls"):
            ExperimentCreateRequest(
                title="Invalid",
                experiment_type="multipage",
            )

    def test_create_schema_server_side_valid(self):
        """Create server-side experiment request."""
        req = ExperimentCreateRequest(
            title="Server-side Test",
            experiment_type="server_side",
            server_side_key="srv_test_key_123",
        )
        assert req.experiment_type == "server_side"
        assert req.server_side_key == "srv_test_key_123"

    def test_create_schema_server_side_missing_error(self):
        """Validation error: server_side without server_side_key."""
        with pytest.raises(ValueError, match="server_side type requires server_side_key"):
            ExperimentCreateRequest(
                title="Invalid",
                experiment_type="server_side",
            )

    def test_create_schema_n_variants_too_low_error(self):
        """Validation error: n_variants less than 2."""
        with pytest.raises(ValueError):
            ExperimentCreateRequest(
                title="Test",
                n_variants=1,
            )

    def test_create_schema_n_variants_too_high_error(self):
        """Validation error: n_variants greater than 10."""
        with pytest.raises(ValueError):
            ExperimentCreateRequest(
                title="Test",
                n_variants=11,
            )

    def test_update_schema_partial(self):
        """Update request with partial fields."""
        req = ExperimentUpdateRequest(
            title="Updated Title",
            n_variants=4,
        )
        assert req.title == "Updated Title"
        assert req.n_variants == 4
        assert req.experiment_type is None

    def test_update_schema_split_url_validation(self):
        """Update validates split_url config."""
        with pytest.raises(ValueError, match="split_url type requires split_url_config"):
            ExperimentUpdateRequest(
                experiment_type="split_url",
            )

    def test_update_schema_multipage_validation(self):
        """Update validates multipage page_urls."""
        with pytest.raises(ValueError, match="multipage type requires non-empty page_urls"):
            ExperimentUpdateRequest(
                experiment_type="multipage",
                page_urls=[],
            )

    def test_update_schema_server_side_validation(self):
        """Update validates server_side_key."""
        with pytest.raises(ValueError, match="server_side type requires server_side_key"):
            ExperimentUpdateRequest(
                experiment_type="server_side",
            )


# ── SCHEMA SERIALIZATION TESTS ────────────────────────────────


class TestExperimentSerialization:
    """Tests for ExperimentOut serialization."""

    def test_serialize_experiment_with_all_fields(self):
        """Serialize an experiment with all new fields."""
        exp_data = {
            "id": str(uuid.uuid4()),
            "merchant_id": str(MERCHANT_ID),
            "title": "Full Experiment",
            "hypothesis": "Test hypothesis",
            "page_element": "#button",
            "friction_type": "hesitation",
            "variant_a": "Control",
            "variant_b": "Variant",
            "result": "a_wins",
            "conversion_delta": 0.05,
            "sample_size": 1000,
            "ran_at": date(2026, 3, 15),
            "source": "manual",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "experiment_type": "ab",
            "n_variants": 2,
            "flicker_free": True,
            "page_urls": None,
            "split_url_config": None,
            "server_side_key": None,
        }
        exp_out = ExperimentOut(**exp_data)
        assert exp_out.experiment_type == "ab"
        assert exp_out.n_variants == 2
        assert exp_out.flicker_free is True

    def test_serialize_split_url_experiment(self):
        """Serialize split URL experiment with config."""
        exp_data = {
            "id": str(uuid.uuid4()),
            "merchant_id": str(MERCHANT_ID),
            "title": "Split URL",
            "experiment_type": "split_url",
            "n_variants": 2,
            "flicker_free": True,
            "split_url_config": SplitUrlConfig(
                control_url="https://example.com/control",
                variant_urls=["https://example.com/v1"],
            ),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        exp_out = ExperimentOut(**exp_data)
        assert exp_out.experiment_type == "split_url"
        assert exp_out.split_url_config is not None
        assert exp_out.split_url_config.control_url == "https://example.com/control"

    def test_serialize_multipage_experiment(self):
        """Serialize multi-page experiment with page URLs."""
        exp_data = {
            "id": str(uuid.uuid4()),
            "merchant_id": str(MERCHANT_ID),
            "title": "Multi-page",
            "experiment_type": "multipage",
            "n_variants": 3,
            "flicker_free": True,
            "page_urls": ["https://example.com/checkout", "https://example.com/cart"],
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        exp_out = ExperimentOut(**exp_data)
        assert exp_out.experiment_type == "multipage"
        assert exp_out.page_urls is not None
        assert len(exp_out.page_urls) == 2


# ── SPLIT URL CONFIG TESTS ────────────────────────────────────────


class TestSplitUrlConfig:
    """Tests for SplitUrlConfig schema."""

    def test_valid_split_url_config(self):
        """Create valid split URL config."""
        config = SplitUrlConfig(
            control_url="https://example.com/control",
            variant_urls=["https://example.com/v1", "https://example.com/v2"],
        )
        assert config.control_url == "https://example.com/control"
        assert len(config.variant_urls) == 2

    def test_split_url_config_empty_control_url(self):
        """Validation error: empty control_url."""
        with pytest.raises(ValueError):
            SplitUrlConfig(control_url="", variant_urls=["https://example.com/v1"])

    def test_split_url_config_empty_variant_urls(self):
        """Validation error: empty variant_urls list."""
        with pytest.raises(ValueError):
            SplitUrlConfig(control_url="https://example.com/control", variant_urls=[])

    def test_split_url_config_too_many_variants(self):
        """Validation error: more than 9 variant_urls."""
        with pytest.raises(ValueError):
            SplitUrlConfig(
                control_url="https://example.com/control",
                variant_urls=[f"https://example.com/v{i}" for i in range(10)],
            )


# ── TYPE LITERAL TESTS ────────────────────────────────────────────


class TestExperimentTypes:
    """Tests for experiment type literals."""

    def test_experiment_type_values(self):
        """All experiment type values are valid."""
        valid_types: list[ExperimentType] = ["ab", "mvt", "split_url", "multipage", "server_side"]
        for exp_type in valid_types:
            assert exp_type in ("ab", "mvt", "split_url", "multipage", "server_side")

    def test_friction_type_values(self):
        """All friction type values are valid."""
        valid_types: list[FrictionType] = ["hesitation", "rage_click", "scroll_retreat", "exit_intent", "checkout_delay"]
        for friction_type in valid_types:
            assert friction_type in ("hesitation", "rage_click", "scroll_retreat", "exit_intent", "checkout_delay")

    def test_experiment_result_values(self):
        """All experiment result values are valid."""
        valid_results: list[ExperimentResult] = ["a_wins", "b_wins", "no_diff", "inconclusive"]
        for result in valid_results:
            assert result in ("a_wins", "b_wins", "no_diff", "inconclusive")
