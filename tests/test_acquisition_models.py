"""Tests for remote_sensing.acquisition.models."""

import json

from remote_sensing.acquisition.models import SceneRecord, dumps


def test_record_to_dict_from_dict_roundtrip() -> None:
    record = SceneRecord(
        scene_id="LC08_191055_20230115",
        satellite="LANDSAT_8",
        date="2023-01-15",
        wrs_path=191,
        wrs_row=55,
        cloud_cover_pct=12.5,
        window="dry",
        selection="best_in_window",
        source_collection="LANDSAT/LC08/C02/T1_L2",
        bands=["SR_B4"],
        crs="EPSG:32631",
        scale_meters=30,
        extra={"landsat_product_id": "LC08_L2SP_191055_20230115_02_T1"},
    )
    restored = SceneRecord.from_dict(record.to_dict())
    assert restored == record


def test_dumps_is_valid_json_with_all_fields(sample_feature) -> None:
    from remote_sensing.acquisition.search import records_from_features

    record = records_from_features([sample_feature], window="dry")[0]
    payload = json.loads(dumps(record))
    assert payload["scene_id"] == "LC08_191055_20230115"
    assert payload["cloud_cover_pct"] == 12.5
    assert payload["window"] == "dry"
