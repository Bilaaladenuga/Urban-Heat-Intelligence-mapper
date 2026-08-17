"""Tests for remote_sensing.acquisition.metadata."""

from remote_sensing.acquisition import metadata
from remote_sensing.acquisition.search import records_from_features


def test_record_roundtrip(sample_feature, tmp_path) -> None:
    record = records_from_features([sample_feature], window="dry")[0]
    record.selection = "best_in_window"
    record.notes = "selected"

    path = metadata.save_record(record, directory=tmp_path)
    assert path.name == f"{record.scene_id}.json"
    loaded = metadata.load_record(path)
    assert loaded == record
    assert loaded.cloud_cover_pct == record.cloud_cover_pct


def test_manifest_roundtrip(sample_feature, tmp_path) -> None:
    records = [records_from_features([sample_feature], window="dry")[0]]
    manifest = tmp_path / "manifest.json"
    metadata.update_manifest(records, manifest_file=manifest)
    loaded = metadata.load_manifest(manifest_file=manifest)
    assert loaded == records


def test_load_manifest_missing_returns_empty(tmp_path) -> None:
    assert metadata.load_manifest(manifest_file=tmp_path / "nope.json") == []
