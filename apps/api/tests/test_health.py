"""Tests for the API health and root endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_app_info() -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["app"] == "Urban Heat Intelligence API"
    assert body["api"] == "/api/v1"


def test_health_returns_ok() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"
    assert "time" in body


def test_unknown_route_returns_404() -> None:
    response = client.get("/api/v1/nope")
    assert response.status_code == 404
