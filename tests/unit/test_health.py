"""Tests for health check endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_readiness_check(client: TestClient) -> None:
    response = client.get("/v1/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AI Inference Gateway"
    assert data["version"] == "0.1.0"
