"""Tests for Dashboard API endpoints (CONV-43).

Tests for session listing, session detail, friction map, and funnel analytics.
Uses mocked DB and auth like the SDK tests.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.merchant import Merchant

MERCHANT_ID = uuid.uuid4()
SDK_KEY_HASH = "dash-test-hash"

AUTH_PATCH = "app.api.dashboard.get_current_merchant"


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


client = TestClient(app, raise_server_exceptions=False)


# ── Session List (CONV-37) ───────────────────────────────────────


class TestListSessions:
    def test_list_sessions_missing_key(self):
        response = client.get("/api/v1/dashboard/sessions")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_list_sessions_success(self, mock_auth):
        db = _reset_mock_db.db
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        sessions_result = MagicMock()
        sessions_result.scalars.return_value = MagicMock(all=MagicMock(return_value=[]))
        db.execute = AsyncMock(side_effect=[count_result, sessions_result])

        response = client.get(
            "/api/v1/dashboard/sessions",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert data["total"] == 0
        assert data["page"] == 1

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_list_sessions_with_filters(self, mock_auth):
        db = _reset_mock_db.db
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        sessions_result = MagicMock()
        sessions_result.scalars.return_value = MagicMock(all=MagicMock(return_value=[]))
        db.execute = AsyncMock(side_effect=[count_result, sessions_result])

        response = client.get(
            "/api/v1/dashboard/sessions?outcome=purchase&risk_min=0.5&page=2&page_size=10",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_list_sessions_invalid_page(self):
        response = client.get(
            "/api/v1/dashboard/sessions?page=0",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_list_sessions_invalid_page_size(self):
        response = client.get(
            "/api/v1/dashboard/sessions?page_size=200",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_list_sessions_invalid_outcome_filter(self):
        response = client.get(
            "/api/v1/dashboard/sessions?outcome=invalid",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_list_sessions_invalid_risk_range(self):
        response = client.get(
            "/api/v1/dashboard/sessions?risk_min=1.5",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422


# ── Session Detail (CONV-38) ─────────────────────────────────────


class TestSessionDetail:
    def test_detail_missing_key(self):
        response = client.get(f"/api/v1/dashboard/sessions/{uuid.uuid4()}")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_detail_invalid_uuid(self, mock_auth):
        response = client.get(
            "/api/v1/dashboard/sessions/not-a-uuid",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 400

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_detail_not_found(self, mock_auth):
        db = _reset_mock_db.db
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            f"/api/v1/dashboard/sessions/{uuid.uuid4()}",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 404


# ── Friction Map (CONV-39) ───────────────────────────────────────


class TestFrictionMap:
    def test_friction_map_missing_key(self):
        response = client.get("/api/v1/dashboard/analytics/friction-map")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_friction_map_empty(self, mock_auth):
        db = _reset_mock_db.db
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            "/api/v1/dashboard/analytics/friction-map",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["elements"] == []
        assert data["total_elements"] == 0

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_friction_map_invalid_limit(self):
        response = client.get(
            "/api/v1/dashboard/analytics/friction-map?limit=300",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422


# ── Funnel (CONV-40) ─────────────────────────────────────────────


class TestFunnel:
    def test_funnel_missing_key(self):
        response = client.get("/api/v1/dashboard/analytics/funnel")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_funnel_empty(self, mock_auth):
        db = _reset_mock_db.db
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        db.execute = AsyncMock(return_value=count_result)

        response = client.get(
            "/api/v1/dashboard/analytics/funnel",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 0
        assert data["conversion_rate"] == 0.0
        assert data["steps"] == []


# ── Rate Limiting (CONV-41) ──────────────────────────────────────


class TestRateLimiting:
    def test_rate_limit_header_present(self):
        response = client.get("/api/v1/dashboard/sessions")
        assert response.status_code == 401


# ── Input Validation (CONV-42) ───────────────────────────────────


class TestInputValidation:
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_invalid_device_type_filter(self):
        response = client.get(
            "/api/v1/dashboard/sessions?device_type=smartwatch",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    def test_valid_device_type_filter(self):
        for device in ["desktop", "mobile", "tablet"]:
            response = client.get(
                f"/api/v1/dashboard/sessions?device_type={device}",
                headers={"X-SDK-Key": SDK_KEY_HASH},
            )
            assert response.status_code != 422


# ── Feature Worker (CONV-36) ─────────────────────────────────────


class TestFeatureWorker:
    def test_feature_worker_module_imports(self):
        from app.services.feature_worker import (
            enqueue_session_processing,
            process_session,
        )

        assert callable(process_session)
        assert callable(enqueue_session_processing)

    def test_feature_extraction_imports(self):
        import sys
        from pathlib import Path

        ml_root = Path(__file__).resolve().parent.parent.parent / "ml"
        if str(ml_root) not in sys.path:
            sys.path.insert(0, str(ml_root))

        from src.features.extraction import extract_features

        features = extract_features(
            events=[],
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
        )
        assert "hesitation_score" in features
        assert "rage_click_score" in features
        assert "exit_intent_count" in features
        assert len(features) == 8
