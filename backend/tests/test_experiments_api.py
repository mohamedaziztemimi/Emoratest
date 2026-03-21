"""Tests for Experiment CRUD & A/B Results API (CONV-38, CONV-41, CONV-46).

Covers: create, list, get, update, delete experiments,
A/B result recording, and statistical significance.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.experiment import Experiment
from app.models.merchant import Merchant

MERCHANT_ID = uuid.uuid4()
SDK_KEY_HASH = "exp-test-hash"
AUTH_PATCH = "app.api.experiments.authenticate_sdk_key"


def make_merchant() -> MagicMock:
    m = MagicMock(spec=Merchant)
    m.id = MERCHANT_ID
    m.email = "test@shop.com"
    m.sdk_key_hash = SDK_KEY_HASH
    m.is_active = True
    return m


def _make_experiment_mock(
    exp_id=None, title="Test Experiment", result=None, delta=None, sample=None
):
    exp = MagicMock(spec=Experiment)
    exp.id = exp_id or uuid.uuid4()
    exp.merchant_id = MERCHANT_ID
    exp.title = title
    exp.hypothesis = "Users will convert more with variant B"
    exp.page_element = "#buy-button"
    exp.friction_type = "hesitation"
    exp.variant_a = "Original"
    exp.variant_b = "New design"
    exp.result = result
    exp.conversion_delta = delta
    exp.sample_size = sample
    exp.ran_at = None
    exp.source = "manual"
    exp.created_at = datetime.now(UTC)
    return exp


@pytest.fixture(autouse=True)
def _reset_mock_db():
    """Reset mock DB state before each test."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.execute = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    _reset_mock_db.db = mock_db
    yield
    pass  # Don't remove override — other test modules may depend on it


client = TestClient(app, raise_server_exceptions=False)


# ── CREATE ────────────────────────────────────────────────────────


class TestCreateExperiment:
    def test_create_missing_key(self):
        response = client.post("/api/v1/experiments", json={"title": "Test"})
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_create_success(self, mock_auth):
        exp = _make_experiment_mock()
        db = _reset_mock_db.db

        # Mock refresh to populate the experiment attributes
        async def fake_refresh(obj, **kw):
            obj.id = exp.id
            obj.merchant_id = exp.merchant_id
            obj.title = "Checkout Button Color Test"
            obj.hypothesis = "Red button converts better"
            obj.page_element = None
            obj.friction_type = "hesitation"
            obj.variant_a = "Blue button"
            obj.variant_b = "Red button"
            obj.result = None
            obj.conversion_delta = None
            obj.sample_size = None
            obj.ran_at = None
            obj.source = "manual"
            obj.created_at = datetime.now(UTC)

        db.refresh = fake_refresh

        response = client.post(
            "/api/v1/experiments",
            json={
                "title": "Checkout Button Color Test",
                "hypothesis": "Red button converts better",
                "friction_type": "hesitation",
                "variant_a": "Blue button",
                "variant_b": "Red button",
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Checkout Button Color Test"
        assert data["friction_type"] == "hesitation"

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_create_missing_title(self, mock_auth):
        response = client.post(
            "/api/v1/experiments",
            json={},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_create_invalid_friction_type(self, mock_auth):
        response = client.post(
            "/api/v1/experiments",
            json={"title": "Test", "friction_type": "invalid_type"},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422


# ── LIST ──────────────────────────────────────────────────────────


class TestListExperiments:
    def test_list_missing_key(self):
        response = client.get("/api/v1/experiments")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_list_empty(self, mock_auth):
        db = _reset_mock_db.db
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        exps_result = MagicMock()
        exps_result.scalars.return_value = MagicMock(all=MagicMock(return_value=[]))
        db.execute = AsyncMock(side_effect=[count_result, exps_result])

        response = client.get(
            "/api/v1/experiments",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["experiments"] == []

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_list_with_results(self, mock_auth):
        db = _reset_mock_db.db
        exp = _make_experiment_mock()
        count_result = MagicMock()
        count_result.scalar.return_value = 1
        exps_result = MagicMock()
        exps_result.scalars.return_value = MagicMock(all=MagicMock(return_value=[exp]))
        db.execute = AsyncMock(side_effect=[count_result, exps_result])

        response = client.get(
            "/api/v1/experiments",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["experiments"]) == 1

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_list_invalid_page(self, mock_auth):
        response = client.get(
            "/api/v1/experiments?page=0",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422


# ── GET ONE ───────────────────────────────────────────────────────


class TestGetExperiment:
    def test_get_missing_key(self):
        response = client.get(f"/api/v1/experiments/{uuid.uuid4()}")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_get_invalid_uuid(self, mock_auth):
        response = client.get(
            "/api/v1/experiments/not-a-uuid",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 400

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_get_not_found(self, mock_auth):
        db = _reset_mock_db.db
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            f"/api/v1/experiments/{uuid.uuid4()}",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 404

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_get_success(self, mock_auth):
        db = _reset_mock_db.db
        exp = _make_experiment_mock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = exp
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            f"/api/v1/experiments/{exp.id}",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Experiment"


# ── UPDATE ────────────────────────────────────────────────────────


class TestUpdateExperiment:
    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_update_not_found(self, mock_auth):
        db = _reset_mock_db.db
        update_result = MagicMock()
        update_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=update_result)

        response = client.put(
            f"/api/v1/experiments/{uuid.uuid4()}",
            json={"title": "Updated"},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 404

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_update_no_fields(self, mock_auth):
        response = client.put(
            f"/api/v1/experiments/{uuid.uuid4()}",
            json={},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 400

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_update_success(self, mock_auth):
        db = _reset_mock_db.db
        exp_id = uuid.uuid4()
        exp = _make_experiment_mock(exp_id=exp_id, title="Updated Title")

        update_result = MagicMock()
        update_result.scalar_one_or_none.return_value = exp_id
        reload_result = MagicMock()
        reload_result.scalar_one.return_value = exp
        db.execute = AsyncMock(side_effect=[update_result, reload_result])

        response = client.put(
            f"/api/v1/experiments/{exp_id}",
            json={"title": "Updated Title"},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"


# ── DELETE ────────────────────────────────────────────────────────


class TestDeleteExperiment:
    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_delete_not_found(self, mock_auth):
        db = _reset_mock_db.db
        delete_result = MagicMock()
        delete_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=delete_result)

        response = client.delete(
            f"/api/v1/experiments/{uuid.uuid4()}",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 404

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_delete_success(self, mock_auth):
        db = _reset_mock_db.db
        exp_id = uuid.uuid4()
        delete_result = MagicMock()
        delete_result.scalar_one_or_none.return_value = exp_id
        db.execute = AsyncMock(return_value=delete_result)

        response = client.delete(
            f"/api/v1/experiments/{exp_id}",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 204


# ── A/B RESULT (CONV-41) ─────────────────────────────────────────


class TestABResult:
    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_record_result_invalid_result_value(self, mock_auth):
        response = client.post(
            f"/api/v1/experiments/{uuid.uuid4()}/result",
            json={
                "result": "winner",
                "conversion_delta": 0.05,
                "sample_size": 1000,
                "ran_at": "2026-03-15",
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_record_result_not_found(self, mock_auth):
        db = _reset_mock_db.db
        update_result = MagicMock()
        update_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=update_result)

        response = client.post(
            f"/api/v1/experiments/{uuid.uuid4()}/result",
            json={
                "result": "a_wins",
                "conversion_delta": 0.05,
                "sample_size": 1000,
                "ran_at": "2026-03-15",
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 404

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_record_result_success(self, mock_auth):
        db = _reset_mock_db.db
        exp_id = uuid.uuid4()
        exp = _make_experiment_mock(exp_id=exp_id, result="a_wins", delta=0.05, sample=1000)

        update_result = MagicMock()
        update_result.scalar_one_or_none.return_value = exp_id
        reload_result = MagicMock()
        reload_result.scalar_one.return_value = exp
        db.execute = AsyncMock(side_effect=[update_result, reload_result])

        response = client.post(
            f"/api/v1/experiments/{exp_id}/result",
            json={
                "result": "a_wins",
                "conversion_delta": 0.05,
                "sample_size": 1000,
                "ran_at": "2026-03-15",
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        assert response.json()["result"] == "a_wins"


# ── STATISTICAL SIGNIFICANCE (CONV-41) ───────────────────────────


class TestABStats:
    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_stats_not_found(self, mock_auth):
        db = _reset_mock_db.db
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            f"/api/v1/experiments/{uuid.uuid4()}/stats",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 404

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_stats_insufficient_data(self, mock_auth):
        db = _reset_mock_db.db
        exp = _make_experiment_mock()
        exp.conversion_delta = None
        exp.sample_size = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = exp
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            f"/api/v1/experiments/{exp.id}/stats",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommendation"] == "insufficient_data"

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_stats_with_data(self, mock_auth):
        db = _reset_mock_db.db
        exp = _make_experiment_mock(result="a_wins", delta=0.05, sample=5000)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = exp
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            f"/api/v1/experiments/{exp.id}/stats",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert "p_value" in data
        assert "is_significant" in data
        assert "power" in data
        assert data["sample_size"] == 5000


# ── EXPERIMENT SERVICE UNIT TESTS ─────────────────────────────────


class TestExperimentService:
    def test_significance_small_sample(self):
        from app.services.experiment_service import compute_ab_significance

        result = compute_ab_significance(conversion_delta=0.05, sample_size=1)
        assert result["recommendation"] == "insufficient_data"

    def test_significance_large_effect(self):
        from app.services.experiment_service import compute_ab_significance

        result = compute_ab_significance(conversion_delta=0.10, sample_size=10000)
        assert result["is_significant"] is True
        assert result["p_value"] is not None
        assert result["p_value"] < 0.05

    def test_significance_no_effect(self):
        from app.services.experiment_service import compute_ab_significance

        result = compute_ab_significance(conversion_delta=0.0001, sample_size=100)
        assert result["is_significant"] is False

    def test_significance_negative_delta(self):
        from app.services.experiment_service import compute_ab_significance

        result = compute_ab_significance(conversion_delta=-0.10, sample_size=10000)
        assert result["is_significant"] is True
        assert result["recommendation"] == "keep_variant_a"
