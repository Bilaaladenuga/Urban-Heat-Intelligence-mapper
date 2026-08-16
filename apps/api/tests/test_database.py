"""Tests for the Supabase/PostGIS database layer.

The integration test at the bottom only runs when a real
``SUPABASE_DB_URL`` is present in the environment (or ``apps/api/.env``).
"""

import pytest
from fastapi.testclient import TestClient

from app.core import db
from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_is_configured_reflects_settings(monkeypatch) -> None:
    monkeypatch.setattr(settings, "supabase_db_url", None)
    assert db.is_configured() is False

    monkeypatch.setattr(settings, "supabase_db_url", "postgresql://user:pass@host:5432/db")
    assert db.is_configured() is True


def test_db_endpoint_reports_not_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "supabase_db_url", None)
    response = client.get("/api/v1/health/db")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] == "not_configured"
    assert body["postgis"] is None


def test_connect_raises_without_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "supabase_db_url", None)
    try:
        with db.connect():
            pass
    except RuntimeError as exc:
        assert "not configured" in str(exc)
    else:
        raise AssertionError("connect() should have raised without a DB URL")


@pytest.mark.skipif(not db.is_configured(), reason="SUPABASE_DB_URL not set")
def test_postgis_available_live() -> None:
    """Integration check: runs once real Supabase credentials are configured."""
    version = db.postgis_version()
    assert version is not None, "PostGIS query failed against the configured database"
