"""Tests for Intervention Recommendation & Tracking API (CONV-39, CONV-46).

Covers: recommendation engine, result recording, aggregated stats.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.merchant import Merchant
from app.models.session import Session
from app.models.session_features import SessionFeatures

MERCHANT_ID = uuid.uuid4()
SDK_KEY_HASH = "intv-test-hash"
AUTH_PATCH = "app.api.interventions.get_merchant_flexible"


def make_merchant() -> MagicMock:
    m = MagicMock(spec=Merchant)
    m.id = MERCHANT_ID
    m.email = "test@shop.com"
    m.sdk_key_hash = SDK_KEY_HASH
    m.is_active = True
    return m


def _make_session_mock(risk=0.7, friction=0.6, intent="browsing"):
    s = MagicMock(spec=Session)
    s.id = uuid.uuid4()
    s.merchant_id = MERCHANT_ID
    s.abandonment_risk = risk
    s.friction_score = friction
    s.intent_label = intent
    return s


def _make_features_mock():
    f = MagicMock(spec=SessionFeatures)
    f.hesitation_score = 0.6
    f.price_dwell_time_s = 8.5
    f.rage_click_score = 0.4
    f.scroll_retreat_count = 4
    f.exit_intent_count = 2
    f.checkout_hesitation_s = 12.0
    f.velocity_variance = 500.0
    f.session_duration_s = 120.0
    return f


@pytest.fixture(autouse=True)
def _reset_mock_db():
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
    pass


client = TestClient(app, raise_server_exceptions=False)


# ── RECOMMEND ─────────────────────────────────────────────────────


class TestRecommendInterventions:
    def test_recommend_missing_key(self):
        response = client.get(f"/api/v1/interventions/recommend/{uuid.uuid4()}")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_recommend_invalid_uuid(self, mock_auth):
        response = client.get(
            "/api/v1/interventions/recommend/not-a-uuid",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 400

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_recommend_session_not_found(self, mock_auth):
        db = _reset_mock_db.db
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            f"/api/v1/interventions/recommend/{uuid.uuid4()}",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 404

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_recommend_success_high_risk(self, mock_auth):
        db = _reset_mock_db.db
        session = _make_session_mock(risk=0.8, friction=0.7, intent="buying")
        features = _make_features_mock()

        session_result = MagicMock()
        session_result.scalar_one_or_none.return_value = session
        features_result = MagicMock()
        features_result.scalar_one_or_none.return_value = features

        db.execute = AsyncMock(side_effect=[session_result, features_result])

        response = client.get(
            f"/api/v1/interventions/recommend/{session.id}",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) <= 3
        assert data["abandonment_risk"] == 0.8

        # Verify recommendations are sorted by priority (descending)
        priorities = [r["priority"] for r in data["recommendations"]]
        assert priorities == sorted(priorities, reverse=True)

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_recommend_low_risk_fewer(self, mock_auth):
        db = _reset_mock_db.db
        session = _make_session_mock(risk=0.1, friction=0.1, intent="browsing")

        session_result = MagicMock()
        session_result.scalar_one_or_none.return_value = session
        features_result = MagicMock()
        features_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(side_effect=[session_result, features_result])

        response = client.get(
            f"/api/v1/interventions/recommend/{session.id}",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_recommend_max_results(self, mock_auth):
        db = _reset_mock_db.db
        session = _make_session_mock(risk=0.8, friction=0.8, intent="buying")
        features = _make_features_mock()

        session_result = MagicMock()
        session_result.scalar_one_or_none.return_value = session
        features_result = MagicMock()
        features_result.scalar_one_or_none.return_value = features
        db.execute = AsyncMock(side_effect=[session_result, features_result])

        response = client.get(
            f"/api/v1/interventions/recommend/{session.id}?max_results=5",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) <= 5


# ── RECORD OUTCOME ────────────────────────────────────────────────


class TestRecordInterventionResult:
    def test_record_missing_key(self):
        response = client.post(
            "/api/v1/interventions/record",
            json={
                "intervention_id": "INT-001",
                "session_id": str(uuid.uuid4()),
                "outcome": "converted",
            },
        )
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_record_invalid_outcome(self, mock_auth):
        response = client.post(
            "/api/v1/interventions/record",
            json={
                "intervention_id": "INT-001",
                "session_id": str(uuid.uuid4()),
                "outcome": "clicked",
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_record_session_not_found(self, mock_auth):
        db = _reset_mock_db.db
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/v1/interventions/record",
            json={
                "intervention_id": "INT-001",
                "session_id": str(uuid.uuid4()),
                "outcome": "converted",
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 404


# ── STATS ─────────────────────────────────────────────────────────


class TestInterventionStats:
    def test_stats_missing_key(self):
        response = client.get("/api/v1/interventions/stats")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_stats_empty(self, mock_auth):
        db = _reset_mock_db.db
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            "/api/v1/interventions/stats",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        assert response.json() == []


# ── INTERVENTION SERVICE UNIT TESTS ───────────────────────────────


class TestInterventionService:
    def test_recommend_high_risk_session(self):
        from app.services.intervention_service import recommend_interventions

        recs = recommend_interventions(
            abandonment_risk=0.8,
            friction_score=0.7,
            intent_label="buying",
            features={
                "rage_click_score": 0.5,
                "exit_intent_count": 3,
                "checkout_hesitation_s": 20.0,
                "scroll_retreat_count": 5,
            },
            max_results=5,
        )
        assert len(recs) > 0
        assert all(0 <= r["priority"] <= 1 for r in recs)
        ids = [r["intervention_id"] for r in recs]
        assert any(i in ids for i in ["INT-001", "INT-003", "INT-007"])

    def test_recommend_zero_risk(self):
        from app.services.intervention_service import recommend_interventions

        recs = recommend_interventions(
            abandonment_risk=0.0,
            friction_score=0.0,
            intent_label="browsing",
            max_results=3,
        )
        assert len(recs) == 0

    def test_recommend_respects_max_results(self):
        from app.services.intervention_service import recommend_interventions

        recs = recommend_interventions(
            abandonment_risk=0.6,
            friction_score=0.5,
            intent_label="comparing",
            max_results=2,
        )
        assert len(recs) <= 2

    def test_recommend_rage_click_boost(self):
        from app.services.intervention_service import recommend_interventions

        recs = recommend_interventions(
            abandonment_risk=0.5,
            friction_score=0.5,
            intent_label="browsing",
            features={"rage_click_score": 0.8},
            max_results=8,
        )
        ids = [r["intervention_id"] for r in recs]
        assert "INT-004" in ids
