"""Tests for the raster tile API endpoints."""

from __future__ import annotations

import pytest
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


class TestRasterScenes:
    """Tests for GET /api/v1/rasters."""

    def test_list_scenes_returns_dict(self, client: TestClient):
        resp = client.get("/api/v1/rasters")
        assert resp.status_code == 200
        data = resp.json()
        assert "scenes" in data
        assert "count" in data
        assert isinstance(data["scenes"], list)

    def test_scene_has_required_fields(self, client: TestClient):
        resp = client.get("/api/v1/rasters")
        data = resp.json()
        if data["count"] > 0:
            scene = data["scenes"][0]
            assert "scene_id" in scene
            assert "bands" in scene
            assert "crs" in scene
            assert "bounds" in scene


class TestRasterTile:
    """Tests for GET /api/v1/rasters/{scene_id}/tiles/{z}/{x}/{y}.png."""

    def test_tile_returns_png(self, client: TestClient):
        resp = client.get(
            "/api/v1/rasters/LC09_191055_20221219/tiles/10/521/493.png",
            params={"band": 1},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        # Should be a real PNG (starts with PNG signature).
        assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"

    def test_tile_outside_extent_returns_transparent(self, client: TestClient):
        """A tile far from Lagos should return a transparent PNG."""
        resp = client.get(
            "/api/v1/rasters/LC09_191055_20221219/tiles/5/16/16.png",
            params={"band": 1},
        )
        # Should return 200 (transparent) or 404.
        assert resp.status_code in (200, 404)

    def test_tile_with_colormap(self, client: TestClient):
        resp = client.get(
            "/api/v1/rasters/LC09_191055_20221219/tiles/10/521/493.png",
            params={"band": 5, "colormap": "thermal"},
        )
        assert resp.status_code == 200
        assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"

    def test_invalid_scene_returns_404(self, client: TestClient):
        resp = client.get(
            "/api/v1/rasters/NONEXISTENT/tiles/10/521/493.png",
            params={"band": 1},
        )
        assert resp.status_code == 404

    def test_invalid_band_returns_error(self, client: TestClient):
        resp = client.get(
            "/api/v1/rasters/LC09_191055_20221219/tiles/10/521/493.png",
            params={"band": 99},
        )
        assert resp.status_code == 422  # validation error
