"""Tests for remote_sensing.acquisition.export."""

from conftest import FakeEE
from remote_sensing.acquisition import config
from remote_sensing.acquisition.export import build_export_task
from remote_sensing.acquisition.models import SceneRecord
from remote_sensing.acquisition.search import records_from_features


def _record(sample_feature) -> SceneRecord:
    return records_from_features([sample_feature], window="dry")[0]


def test_build_export_task_parameters(sample_feature) -> None:
    ee = FakeEE()
    record = _record(sample_feature)
    task = build_export_task(ee, scene=record, geometry="GEO")
    assert task.kwargs["description"] == record.scene_id
    assert task.kwargs["fileNamePrefix"] == record.scene_id
    assert task.kwargs["folder"] == config.DRIVE_FOLDER
    assert task.kwargs["region"] == "GEO"
    assert task.kwargs["scale"] == config.SCALE_METERS
    assert task.kwargs["crs"] == config.EXPORT_CRS
    assert task.kwargs["fileFormat"] == config.EXPORT_FORMAT
    assert task.kwargs["formatOptions"] == {"cloudOptimized": True}
    # The image select call used the recorded bands.
    image = task.kwargs["image"]
    assert image.image_id == record.scene_id
    assert image.selected == record.bands


def test_start_export_starts_task(sample_feature) -> None:
    from remote_sensing.acquisition.export import start_export

    ee = FakeEE()
    task = build_export_task(ee, scene=_record(sample_feature), geometry="GEO")
    task_id = start_export(ee, task)
    assert task.started is True
    assert task_id == task.id
