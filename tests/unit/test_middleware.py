"""Tests for middleware stack."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_request_id_header_added(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 36  # UUID length


def test_request_id_header_preserved(client: TestClient) -> None:
    custom_id = "my-custom-request-id-123"
    response = client.get("/v1/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


def test_timing_header_added(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert "X-Response-Time-Ms" in response.headers
    duration = float(response.headers["X-Response-Time-Ms"])
    assert duration >= 0.0


def test_cors_headers_present(client: TestClient) -> None:
    response = client.options(
        "/v1/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AI Inference Gateway"
    assert data["version"] == "0.1.0"
