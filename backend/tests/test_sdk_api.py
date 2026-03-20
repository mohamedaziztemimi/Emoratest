"""Tests for SDK API endpoints (CONV-35).

Uses FastAPI TestClient with mocked database and auth.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.merchant import Merchant

# ── Helpers ──────────────────────────────────────────────────────

MERCHANT_ID = uuid.uuid4()
SDK_KEY_HASH = "abc123hashvalue"


def make_merchant() -> MagicMock:
    m = MagicMock(spec=Merchant)
    m.id = MERCHANT_ID
    m.email = "test@shop.com"
    m.sdk_key_hash = SDK_KEY_HASH
    m.is_active = True
    return m


# Mock DB
mock_db = AsyncMock()
mock_db.add = MagicMock()
mock_db.add_all = MagicMock()
mock_db.commit = AsyncMock()
mock_db.execute = AsyncMock()


async def override_get_db():
    yield mock_db


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Patch path for authenticate_sdk_key (it's called in app.api.sdk)
AUTH_PATCH = "app.api.sdk.authenticate_sdk_key"


# ── Session Create ───────────────────────────────────────────────


class TestCreateSession:
    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_create_session_success(self, mock_auth):
        response = client.post(
            "/api/v1/sessions",
            json={
                "merchant_id": str(MERCHANT_ID),
                "page_url": "https://shop.com/cart",
                "started_at": "2026-01-01T00:00:00Z",
                "country_code": "US",
                "device_type": "desktop",
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        uuid.UUID(data["session_id"])  # validates UUID format

    def test_create_session_missing_sdk_key(self):
        response = client.post(
            "/api/v1/sessions",
            json={
                "merchant_id": str(MERCHANT_ID),
                "page_url": "https://shop.com/cart",
                "started_at": "2026-01-01T00:00:00Z",
            },
        )
        assert response.status_code == 401

    def test_create_session_invalid_body(self):
        response = client.post(
            "/api/v1/sessions",
            json={},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    def test_create_session_invalid_device_type(self):
        response = client.post(
            "/api/v1/sessions",
            json={
                "merchant_id": str(MERCHANT_ID),
                "page_url": "https://shop.com/cart",
                "started_at": "2026-01-01T00:00:00Z",
                "device_type": "smartwatch",
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422


# ── Session End ──────────────────────────────────────────────────


class TestEndSession:
    def test_end_session_missing_key(self):
        response = client.put(f"/api/v1/sessions/{uuid.uuid4()}/end")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_end_session_success(self, mock_auth):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.uuid4()
        mock_db.execute.return_value = mock_result

        response = client.put(
            f"/api/v1/sessions/{uuid.uuid4()}/end",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ended"

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_end_session_not_found(self, mock_auth):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.put(
            f"/api/v1/sessions/{uuid.uuid4()}/end",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 404

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_end_session_invalid_uuid(self, mock_auth):
        response = client.put(
            "/api/v1/sessions/not-a-uuid/end",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 400


# ── Session Outcome ──────────────────────────────────────────────


class TestUpdateOutcome:
    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_outcome_purchase(self, mock_auth):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.uuid4()
        mock_db.execute.return_value = mock_result

        response = client.put(
            f"/api/v1/sessions/{uuid.uuid4()}/outcome",
            json={"outcome": "purchase"},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        assert response.json()["outcome"] == "purchase"

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_outcome_abandon(self, mock_auth):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.uuid4()
        mock_db.execute.return_value = mock_result

        response = client.put(
            f"/api/v1/sessions/{uuid.uuid4()}/outcome",
            json={"outcome": "abandon"},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        assert response.json()["outcome"] == "abandon"

    def test_outcome_invalid_value(self):
        response = client.put(
            f"/api/v1/sessions/{uuid.uuid4()}/outcome",
            json={"outcome": "returned"},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    def test_outcome_missing_key(self):
        response = client.put(
            f"/api/v1/sessions/{uuid.uuid4()}/outcome",
            json={"outcome": "purchase"},
        )
        assert response.status_code == 401


# ── Event Batch ──────────────────────────────────────────────────


class TestIngestEvents:
    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_batch_success(self, mock_auth):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.uuid4()
        mock_db.execute.return_value = mock_result

        response = client.post(
            "/api/v1/events/batch",
            json={
                "session_id": str(uuid.uuid4()),
                "events": [
                    {"type": "click", "ts": "2026-01-01T00:00:00Z", "x": 50, "y": 75},
                    {
                        "type": "mouse_move", "ts": "2026-01-01T00:00:01Z",
                        "x": 100, "y": 200, "velocity": 2.5,
                    },
                ],
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["count"] == 2

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_batch_all_event_types(self, mock_auth):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.uuid4()
        mock_db.execute.return_value = mock_result

        events = [
            {"type": "mouse_move", "ts": "2026-01-01T00:00:00Z", "x": 10, "y": 20, "velocity": 1.5},
            {"type": "click", "ts": "2026-01-01T00:00:01Z", "x": 50, "y": 75},
            {"type": "scroll", "ts": "2026-01-01T00:00:02Z"},
            {"type": "exit_intent", "ts": "2026-01-01T00:00:03Z"},
            {"type": "visibility", "ts": "2026-01-01T00:00:04Z"},
        ]
        response = client.post(
            "/api/v1/events/batch",
            json={"session_id": str(uuid.uuid4()), "events": events},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        assert response.json()["count"] == 5

    def test_batch_invalid_event_type(self):
        response = client.post(
            "/api/v1/events/batch",
            json={
                "session_id": str(uuid.uuid4()),
                "events": [{"type": "keyboard", "ts": "2026-01-01T00:00:00Z"}],
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    def test_batch_empty_events(self):
        response = client.post(
            "/api/v1/events/batch",
            json={"session_id": str(uuid.uuid4()), "events": []},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    def test_batch_too_many_events(self):
        events = [{"type": "click", "ts": "2026-01-01T00:00:00Z"} for _ in range(201)]
        response = client.post(
            "/api/v1/events/batch",
            json={"session_id": str(uuid.uuid4()), "events": events},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    def test_batch_missing_sdk_key(self):
        response = client.post(
            "/api/v1/events/batch",
            json={
                "session_id": str(uuid.uuid4()),
                "events": [{"type": "click", "ts": "2026-01-01T00:00:00Z"}],
            },
        )
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_batch_session_not_found(self, mock_auth):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.post(
            "/api/v1/events/batch",
            json={
                "session_id": str(uuid.uuid4()),
                "events": [{"type": "click", "ts": "2026-01-01T00:00:00Z"}],
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 404


# ── SDK Key Auth ─────────────────────────────────────────────────


class TestSDKKeyAuth:
    def test_missing_key_returns_401(self):
        response = client.post(
            "/api/v1/sessions",
            json={
                "merchant_id": str(MERCHANT_ID),
                "page_url": "https://shop.com",
                "started_at": "2026-01-01T00:00:00Z",
            },
        )
        assert response.status_code == 401
        assert "Missing SDK key" in response.json()["detail"]


# ── Schema Validation ────────────────────────────────────────────


class TestSchemaValidation:
    def test_element_id_max_length(self):
        response = client.post(
            "/api/v1/events/batch",
            json={
                "session_id": str(uuid.uuid4()),
                "events": [
                    {"type": "click", "ts": "2026-01-01T00:00:00Z", "element_id": "a" * 129}
                ],
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    def test_outcome_must_be_purchase_or_abandon(self):
        response = client.put(
            f"/api/v1/sessions/{uuid.uuid4()}/outcome",
            json={"outcome": "unknown"},
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 422

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    def test_event_metadata_dict(self, mock_auth):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.uuid4()
        mock_db.execute.return_value = mock_result

        response = client.post(
            "/api/v1/events/batch",
            json={
                "session_id": str(uuid.uuid4()),
                "events": [
                    {
                        "type": "scroll",
                        "ts": "2026-01-01T00:00:00Z",
                        "metadata": {"direction": "down", "delta": 150},
                    }
                ],
            },
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
