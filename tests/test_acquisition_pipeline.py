"""Tests for remote_sensing.acquisition.pipeline."""

import json

import pytest
from conftest import FakeEE
from remote_sensing.acquisition import config, pipeline


def test_dry_run_prints_plan(capsys) -> None:
    code = pipeline.main(["--dry-run", "--year", "2023"])
    assert code == 0
    out = capsys.readouterr().out
    assert "ACQUISITION PLAN" in out
    assert "LANDSAT/LC08/C02/T1_L2" in out
    assert "WRS path/row" in out and "191/55" in out
    assert "2022-11-01" in out and "2023-03-31" in out  # dry window
    assert "2023-04-01" in out and "2023-10-31" in out  # wet window
    assert "earthengine authenticate" in out


def test_plan_uses_both_windows(sample_feature) -> None:
    dry = dict(sample_feature)
    wet = dict(sample_feature)
    wet["id"] = "LC09_191055_20230610"
    wet["properties"] = {**wet["properties"], "system:index": "LC09_191055_20230610",
                         "DATE_ACQUIRED": "2023-06-10", "SPACECRAFT_ID": "LANDSAT_9"}
    ee = FakeEE([{"features": [dry]}, {"features": [wet]}])
    geojson = json.loads(config.GEOMETRY_SOURCE.read_text(encoding="utf-8"))
    records = pipeline.plan(ee, year=2023,
                            cloud_threshold_pct=config.CLOUD_THRESHOLD_PCT,
                            geometry_geojson=geojson)
    assert len(records) == 2
    assert records[0] is not None and records[0].window == "dry"
    assert records[1] is not None and records[1].window == "wet"
    assert records[1].scene_id == "LC09_191055_20230610"


def test_missing_geometry_raises(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "GEOMETRY_SOURCE", tmp_path / "missing.geojson")
    with pytest.raises(FileNotFoundError):
        pipeline.main(["--dry-run", "--year", "2023"])

