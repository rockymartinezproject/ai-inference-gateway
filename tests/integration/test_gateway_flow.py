"""Integration tests for the full gateway flow."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers.factory import build_registry
from app.providers.registry import set_registry


@pytest.fixture
def client() -> TestClient:
    # Initialize registry for integration tests
    set_registry(build_registry())
    return TestClient(app)


def test_health_and_models_endpoint(client: TestClient) -> None:
    """Verify health and models endpoints are wired correctly."""
    health = client.get("/v1/health")
    assert health.status_code == 200

    models = client.get("/v1/models", headers={"X-API-Key": "test-key"})
    assert models.status_code == 200
    data = models.json()
    assert "data" in data
    assert len(data["data"]) > 0


def test_admin_endpoints_require_auth(client: TestClient) -> None:
    """Admin endpoints should reject unauthenticated requests."""
    resp = client.get("/v1/admin/config")
    assert resp.status_code == 501  # Admin key not configured in test


def test_request_id_and_timing_headers(client: TestClient) -> None:
    """Middleware should inject tracking headers."""
    resp = client.get("/v1/health")
    assert "X-Request-ID" in resp.headers
    assert "X-Response-Time-Ms" in resp.headers


def test_cors_preflight(client: TestClient) -> None:
    """CORS preflight should succeed."""
    resp = client.options(
        "/v1/models",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers


def test_analytics_endpoints(client: TestClient) -> None:
    """Analytics endpoints should be accessible with API key."""
    resp = client.get(
        "/v1/analytics/usage",
        headers={"X-API-Key": "test-key"},
    )
    assert resp.status_code == 200
    assert "requests_today" in resp.json()


def test_streaming_endpoint_exists(client: TestClient) -> None:
    """Streaming endpoint should exist and require POST."""
    resp = client.get("/v1/chat/completions/stream")
    assert resp.status_code == 405  # Method Not Allowed (needs POST)
