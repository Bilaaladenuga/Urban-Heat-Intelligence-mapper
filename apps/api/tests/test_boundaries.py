"""Tests for Phase 2 boundary handling.

The live PostGIS upsert test only runs when a real ``SUPABASE_DB_URL``
is configured; the extraction logic is unit-tested with fixtures.
"""

import pytest
from fastapi.testclient import TestClient

from app.core import db
from app.core.config import settings
from app.main import app
from app.services.boundaries import (
    extract_lgas,
    extract_state,
    feature_to_feature_collection,
    osm_elements_to_features,
)

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


def _osm_elements() -> list[dict]:
    return [
        {
            "type": "node",
            "id": 1001,
            "lat": 6.52,
            "lon": 3.38,
            "tags": {"name": "Ikeja", "place": "suburb"},
        },
        {
            "type": "node",
            "id": 1002,
            "lat": 6.45,
            "lon": 3.42,
            "tags": {"name": "Victoria Island", "place": "suburb"},
        },
        # Unclosed way — must be skipped.
        {
            "type": "way",
            "id": 2001,
            "tags": {"name": "Broken Ring", "place": "neighbourhood"},
            "geometry": [{"lat": 6.5, "lon": 3.3}, {"lat": 6.6, "lon": 3.4}],
        },
        # Closed way — becomes a Polygon.
        {
            "type": "way",
            "id": 2002,
            "tags": {"name": "Eko Atlantic", "place": "suburb"},
            "geometry": [
                {"lat": 6.42, "lon": 3.41},
                {"lat": 6.43, "lon": 3.42},
                {"lat": 6.42, "lon": 3.43},
                {"lat": 6.41, "lon": 3.42},
                {"lat": 6.42, "lon": 3.41},
            ],
        },
        # Untagged element — must be skipped.
        {"type": "node", "id": 1003, "lat": 6.5, "lon": 3.5, "tags": {}},
    ]


def test_osm_elements_to_features_nodes_and_polygon() -> None:
    features = osm_elements_to_features(_osm_elements())
    by_name = {f["properties"]["name"]: f for f in features}
    assert by_name["Ikeja"]["geometry"] == {"type": "Point", "coordinates": [3.38, 6.52]}
    assert by_name["Ikeja"]["properties"]["osm_id"] == 1001
    assert by_name["Eko Atlantic"]["geometry"]["type"] == "Polygon"
    assert len(by_name["Eko Atlantic"]["geometry"]["coordinates"][0]) == 5
    # Unclosed way and untagged node dropped.
    assert "Broken Ring" not in by_name


def test_osm_elements_to_features_polygon_wins_on_duplicate_name() -> None:
    elements = _osm_elements() + [
        {
            "type": "node",
            "id": 1004,
            "lat": 6.42,
            "lon": 3.42,
            "tags": {"name": "Eko Atlantic", "place": "suburb"},
        }
    ]
    features = osm_elements_to_features(elements)
    by_name = {f["properties"]["name"]: f for f in features}
    assert by_name["Eko Atlantic"]["geometry"]["type"] == "Polygon"
    assert by_name["Eko Atlantic"]["properties"]["osm_type"] == "way"


def test_osm_elements_to_features_polygon_wins_regardless_of_order() -> None:
    elements = _osm_elements()
    # Node listed first (as in the fixture) — way must still win.
    node_first = [e for e in elements if e["type"] == "node"] + [
        e for e in elements if e["type"] == "way"
    ]
    by_name = {f["properties"]["name"]: f for f in osm_elements_to_features(node_first)}
    assert by_name["Eko Atlantic"]["geometry"]["type"] == "Polygon"


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


@pytest.mark.skipif(not db.is_configured(), reason="SUPABASE_DB_URL not set")
def test_neighborhoods_returns_features_live() -> None:
    """Integration check: the OSM neighborhood layer is served."""
    response = client.get("/api/v1/boundaries/neighborhoods")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) >= 50
    names = {f["properties"]["name"] for f in body["features"]}
    assert "Surulere" in names and "Victoria Island" in names and "Makoko" in names
