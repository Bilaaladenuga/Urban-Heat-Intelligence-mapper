"""Tests for remote_sensing.acquisition.search."""

import pytest
from conftest import FakeEE
from remote_sensing.acquisition import config
from remote_sensing.acquisition.search import (
    build_search_query,
    plan_window,
    records_from_features,
    select_best,
    window_date_range,
)


def test_window_date_range_dry_crosses_year() -> None:
    assert window_date_range("dry", 2023) == ("2022-11-01", "2023-03-31")


def test_window_date_range_wet() -> None:
    assert window_date_range("wet", 2023) == ("2023-04-01", "2023-10-31")


def test_window_date_range_unknown_window_raises() -> None:
    with pytest.raises(KeyError):
        window_date_range("monsoon", 2023)


def test_records_from_features_maps_fields(sample_feature) -> None:
    records = records_from_features([sample_feature], window="dry")
    assert len(records) == 1
    record = records[0]
    assert record.scene_id == "LC08_191055_20230115"
    assert record.satellite == "LANDSAT_8"
    assert record.date == "2023-01-15"
    assert record.cloud_cover_pct == 12.5
    assert record.window == "dry"
    assert record.bands == config.BANDS
    assert record.crs == config.EXPORT_CRS
    assert record.scale_meters == config.SCALE_METERS
    assert record.extra["landsat_product_id"].startswith("LC08_L2SP")


def test_records_from_features_skips_idless(sample_feature) -> None:
    feature = dict(sample_feature)
    del feature["id"]
    feature["properties"] = {"SPACECRAFT_ID": "LANDSAT_8"}
    assert records_from_features([feature], window="dry") == []


def test_select_best_picks_lowest_cloud(sample_feature) -> None:
    cloudy = _variant(sample_feature, "LC08_191055_20230201",
                      cloud=55.0, date="2023-02-01")
    clear = _variant(sample_feature, "LC08_191055_20230210",
                     cloud=8.0, date="2023-02-10")
    records = records_from_features([cloudy, clear], window="dry")
    best = select_best(records)
    assert best is not None
    assert best.scene_id == "LC08_191055_20230210"


def test_select_best_empty_returns_none() -> None:
    assert select_best([]) is None


def test_build_search_query_applies_filters() -> None:
    chain = FakeEE()
    _ = build_search_query(chain, geometry="GEO", window="wet", year=2023,
                           max_cloud_pct=10.0)
    assert chain.collections_seen()[:2] == config.COLLECTIONS
    built = chain.ImageCollection(config.COLLECTIONS[0]).filters
    ops = [f[0] for f in built]
    assert ops == ["filterBounds", "filterDate", "filter", "filter", "filter"]
    path_filter = built[2]
    row_filter = built[3]
    cloud_filter = built[4]
    assert path_filter[1].op == "eq" and path_filter[1].args == ("WRS_PATH", 191)
    assert row_filter[1].op == "eq" and row_filter[1].args == ("WRS_ROW", 55)
    assert cloud_filter[1].op == "lte" and cloud_filter[1].args[1] == 10.0
    # Date range matches the wet window for 2023.
    assert built[1][1:] == ("2023-04-01", "2023-10-31")


def test_build_search_query_without_cloud_filter() -> None:
    chain = FakeEE()
    _ = build_search_query(chain, geometry="GEO", window="wet", year=2023,
                           max_cloud_pct=None)
    filters = chain.ImageCollection(config.COLLECTIONS[0]).filters
    ops = [f[0] for f in filters]
    assert ops == ["filterBounds", "filterDate", "filter", "filter"]
    # No cloud-cover ceiling filter applied.
    assert all(f[1].op != "lte" for f in filters if f[0] == "filter")


def test_plan_window_selects_within_threshold(sample_feature) -> None:
    clear = dict(sample_feature)
    clear["properties"] = {**clear["properties"], "CLOUD_COVER": 5.0}
    clear["id"] = clear["properties"]["system:index"]
    ee = FakeEE([{"features": [sample_feature, clear]}])
    record, messages = plan_window(
        ee, geometry="GEO", window="dry", year=2023,
        cloud_threshold_pct=config.CLOUD_THRESHOLD_PCT,
    )
    assert record is not None
    assert record.selection == "best_in_window"
    assert record.cloud_above_threshold is False
    assert record.scene_id == "LC08_191055_20230115"
    assert any("selected" in m for m in messages)


def _variant(sample_feature, scene_id: str, *, cloud: float, date: str) -> dict:
    feature = dict(sample_feature)
    feature["id"] = scene_id
    feature["properties"] = {
        **feature["properties"],
        "CLOUD_COVER": cloud,
        "DATE_ACQUIRED": date,
        "system:index": scene_id,
    }
    return feature


def test_plan_window_fallback_above_threshold(sample_feature) -> None:
    cloudy = _variant(sample_feature, "LC08_191055_20230501",
                      cloud=40.0, date="2023-05-01")
    # First query (within threshold) returns nothing; second (no ceiling)
    # returns the cloudy scene -> documented fallback.
    ee = FakeEE([{"features": []}, {"features": [cloudy]}])
    record, messages = plan_window(
        ee, geometry="GEO", window="wet", year=2023,
        cloud_threshold_pct=config.CLOUD_THRESHOLD_PCT,
    )
    assert record is not None
    assert record.selection == "fallback_above_threshold"
    assert record.cloud_above_threshold is True
    assert "fallback" in record.notes.lower() or "cloud" in record.notes.lower()
    assert messages


def test_plan_window_no_scenes_returns_none() -> None:
    ee = FakeEE([{"features": []}, {"features": []}])
    record, messages = plan_window(
        ee, geometry="GEO", window="dry", year=2023,
        cloud_threshold_pct=config.CLOUD_THRESHOLD_PCT,
    )
    assert record is None
    assert any("no scenes" in m for m in messages)
