"""Tests for Cohort & Segment Analytics API (CONV-40, CONV-46).

Covers: cohort analysis, risk distribution, security headers.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.merchant import Merchant

MERCHANT_ID = uuid.uuid4()
SDK_KEY_HASH = "analytics-test-hash"
AUTH_PATCH = "app.services.sdk_auth.authenticate_sdk_key"


def make_merchant() -> MagicMock:
    m = MagicMock(spec=Merchant)
    m.id = MERCHANT_ID
    m.email = "test@shop.com"
    m.sdk_key_hash = SDK_KEY_HASH
    m.is_active = True
    return m


@pytest.fixture(autouse=True)
def _reset_mock_db():
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    _reset_mock_db.db = mock_db
    yield
    pass


client = TestClient(app, raise_server_exceptions=False)


# ── COHORT ANALYSIS ───────────────────────────────────────────────


class TestCohortAnalytics:
    def test_cohorts_missing_key(self):
        response = client.get("/api/v1/analytics/cohorts?dimension=device_type")
        assert response.status_code == 401

    def test_cohorts_missing_dimension(self):
        response = client.get(
            "/api/v1/analytics/cohorts",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    def test_cohorts_invalid_dimension(self):
        response = client.get(
            "/api/v1/analytics/cohorts?dimension=email",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_cohorts_empty(self, mock_auth):
        db = _reset_mock_db.db
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            "/api/v1/analytics/cohorts?dimension=device_type",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["dimension"] == "device_type"
        assert data["buckets"] == []
        assert data["total_sessions"] == 0

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_cohorts_valid_dimensions(self, mock_auth):
        db = _reset_mock_db.db
        for dim in ["device_type", "country_code", "outcome", "intent_label"]:
            mock_result = MagicMock()
            mock_result.all.return_value = []
            db.execute = AsyncMock(return_value=mock_result)

            response = client.get(
                f"/api/v1/analytics/cohorts?dimension={dim}",
                headers={"X-SDK-Key": SDK_KEY_HASH},
            )
            assert response.status_code == 200, f"Failed for dimension={dim}"


# ── RISK DISTRIBUTION ────────────────────────────────────────────


class TestRiskDistribution:
    def test_risk_dist_missing_key(self):
        response = client.get("/api/v1/analytics/risk-distribution")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_risk_dist_empty(self, mock_auth):
        db = _reset_mock_db.db
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            "/api/v1/analytics/risk-distribution",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 0
        assert data["buckets"] == []

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_risk_dist_with_data(self, mock_auth):
        db = _reset_mock_db.db
        # Simulate scored sessions
        rows = [
            MagicMock(abandonment_risk=0.1, outcome="purchase"),
            MagicMock(abandonment_risk=0.3, outcome="unknown"),
            MagicMock(abandonment_risk=0.7, outcome="abandon"),
            MagicMock(abandonment_risk=0.9, outcome="abandon"),
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = rows
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            "/api/v1/analytics/risk-distribution?buckets=5",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 4
        assert len(data["buckets"]) == 5
        assert data["avg_risk"] is not None

    def test_risk_dist_invalid_buckets(self):
        response = client.get(
            "/api/v1/analytics/risk-distribution?buckets=1",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    def test_risk_dist_too_many_buckets(self):
        response = client.get(
            "/api/v1/analytics/risk-distribution?buckets=25",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422


# ── SECURITY TESTS ────────────────────────────────────────────────


class TestSecurityHeaders:
    def test_health_has_security_headers(self):
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert "X-Request-ID" in response.headers

    def test_request_id_propagated(self):
        response = client.get(
            "/health", headers={"X-Request-ID": "test-123"}
        )
        assert response.headers.get("X-Request-ID") == "test-123"
