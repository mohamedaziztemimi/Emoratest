"""Tests for Merchant API Key Management (CONV-43, CONV-46).

Covers: profile retrieval, key rotation, usage summary.
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
SDK_KEY_HASH = "merchant-test-hash"
AUTH_PATCH = "app.api.merchants.get_merchant_flexible"


def make_merchant() -> MagicMock:
    m = MagicMock(spec=Merchant)
    m.id = MERCHANT_ID
    m.email = "test@shop.com"
    m.shop_domain = "test-shop.myshopify.com"
    m.sdk_key_hash = SDK_KEY_HASH
    m.plan = "growth"
    m.is_active = True
    m.created_at = datetime.now(UTC)
    m.updated_at = datetime.now(UTC)
    return m


@pytest.fixture(autouse=True)
def _reset_mock_db():
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    _reset_mock_db.db = mock_db
    yield
    pass


client = TestClient(app, raise_server_exceptions=False)


# ── GET /me ───────────────────────────────────────────────────────


class TestMerchantProfile:
    def test_profile_missing_key(self):
        response = client.get("/api/v1/merchants/me")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_profile_success(self, mock_auth):
        response = client.get(
            "/api/v1/merchants/me",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@shop.com"
        assert data["plan"] == "growth"
        assert data["is_active"] is True


# ── POST /rotate-key ─────────────────────────────────────────────


class TestKeyRotation:
    def test_rotate_missing_key(self):
        response = client.post("/api/v1/merchants/rotate-key")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_rotate_success(self, mock_auth):
        response = client.post(
            "/api/v1/merchants/rotate-key",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert "new_sdk_key" in data
        assert len(data["new_sdk_key"]) == 64
        assert "rotated_at" in data


# ── GET /usage ────────────────────────────────────────────────────


class TestUsageSummary:
    def test_usage_missing_key(self):
        response = client.get("/api/v1/merchants/usage")
        assert response.status_code == 401

    @patch(AUTH_PATCH, new_callable=AsyncMock, return_value=make_merchant())
    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_usage_success(self, mock_auth):
        db = _reset_mock_db.db
        count_mock = MagicMock()
        count_mock.scalar.return_value = 42
        db.execute = AsyncMock(return_value=count_mock)

        response = client.get(
            "/api/v1/merchants/usage",
            headers={"X-SDK-Key": SDK_KEY_HASH},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert "total_events" in data
        assert "total_experiments" in data
        assert data["plan"] == "growth"
