"""Tests for authentication dependencies."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_without_api_key_succeeds(client: TestClient) -> None:
    """Health endpoint should be public."""
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_admin_config_without_key_fails(client: TestClient) -> None:
    response = client.get("/v1/admin/config")
    assert response.status_code == 501  # Admin key not configured in tests


def test_admin_config_with_wrong_key_fails(client: TestClient) -> None:
    original_key = settings.admin_api_key
    settings.admin_api_key = "real-admin-key"
    try:
        response = client.get(
            "/v1/admin/config",
            headers={"X-Admin-Key": "wrong-key"},
        )
        assert response.status_code == 403
    finally:
        settings.admin_api_key = original_key


def test_admin_provider_health_without_key_fails(client: TestClient) -> None:
    response = client.get("/v1/admin/providers/health")
    assert response.status_code == 501
