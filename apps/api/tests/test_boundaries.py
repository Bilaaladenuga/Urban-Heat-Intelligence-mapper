"""Tests for Phase 2 boundary handling.

The live PostGIS upsert test only runs when a real ``SUPABASE_DB_URL``
is configured; the extraction logic is unit-tested with fixtures.
"""

import pytest
from fastapi.testclient import TestClient

from app.core import db
from app.core.config import settings
from app.main import app
from app.services.boundaries import extract_lgas, extract_state, feature_to_feature_collection

client = TestClient(app)


def _sample_states() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "adm0_name": "Nigeria",
                    "adm1_name": "Ogun",
                    "adm1_pcode": "NG001",
                    "adm2_name": None,
                    "area_sqkm": 100.0,
                },
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
            },
            {
                "type": "Feature",
                "properties": {
                    "adm0_name": "Nigeria",
                    "adm1_name": "Lagos",
                    "adm1_pcode": "NG025",
                    "adm2_name": None,
                    "area_sqkm": 3671.0,
                },
                "geometry": {"type": "Polygon", "coordinates": [[[3, 6], [4, 6], [4, 7], [3, 6]]]},
            },
            # An LGA row under Lagos also carries adm1_name — must be excluded.
            {
                "type": "Feature",
                "properties": {
                    "adm0_name": "Nigeria",
                    "adm1_name": "Lagos",
                    "adm1_pcode": "NG025",
                    "adm2_name": "Ikeja",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[3, 6], [3.5, 6], [3.5, 6.5], [3, 6]]],
                },
            },
        ],
    }


def test_extract_state_finds_lagos() -> None:
    feature = extract_state(_sample_states(), "Lagos")
    assert feature is not None
    assert feature["properties"]["adm1_pcode"] == "NG025"
    assert feature["geometry"]["type"] == "Polygon"


def test_extract_state_excludes_lga_rows() -> None:
    feature = extract_state(_sample_states(), "Lagos")
    assert feature is not None
    assert feature["properties"].get("adm2_name") is None


def test_extract_state_missing_returns_none() -> None:
    assert extract_state(_sample_states(), "Kano") is None


def test_extract_lgas_returns_only_child_rows() -> None:
    lgas = extract_lgas(_sample_states(), "Lagos")
    assert len(lgas) == 1
    assert lgas[0]["properties"]["adm2_name"] == "Ikeja"


def test_extract_lgas_empty_for_other_state() -> None:
    assert extract_lgas(_sample_states(), "Ogun") == []


def test_feature_collection_wraps_single_feature() -> None:
    fc = feature_to_feature_collection(_sample_states()["features"][1])
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1


def test_city_boundary_503_when_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "supabase_db_url", None)
    response = client.get("/api/v1/boundaries/city")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database not configured"


@pytest.mark.skipif(not db.is_configured(), reason="SUPABASE_DB_URL not set")
def test_city_boundary_returns_geojson_live() -> None:
    """Integration check against the configured Supabase/PostGIS instance."""
    response = client.get("/api/v1/boundaries/city")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 1
    props = body["features"][0]["properties"]
    assert props.get("adm1_name") == "Lagos"
    assert body["features"][0]["geometry"]["type"] in ("Polygon", "MultiPolygon")


@pytest.mark.skipif(not db.is_configured(), reason="SUPABASE_DB_URL not set")
def test_lgas_returns_twenty_features_live() -> None:
    """Integration check: all 20 Lagos LGAs are served."""
    response = client.get("/api/v1/boundaries/lgas")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 20
    names = {f["properties"]["adm2_name"] for f in body["features"]}
    assert "Ikeja" in names and "Eti-Osa" in names and "Badagry" in names
