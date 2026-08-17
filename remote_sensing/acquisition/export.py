"""Export a selected scene from Earth Engine (Phase 3 — acquisition).

Builds a cloud-optimized GeoTIFF export of the analysis bands for one
scene, clipped to the study area, in the analysis CRS (UTM 31N). The
export goes to a Google Drive folder; the user downloads it from there
(or a later script pulls it via the Drive API).
"""

from __future__ import annotations

from . import config


def build_export_task(ee, *, scene, geometry) -> object:
    """Return an ``ee.Export.image.toDrive`` task for one scene.

    ``scene`` is a :class:`~remote_sensing.acquisition.models.SceneRecord`
    whose bands/CRS/scale fields were captured at selection time.
    """
    asset_id = scene.extra.get("asset_id") or f"{scene.source_collection}/{scene.scene_id}"
    image = ee.Image(asset_id).select(scene.bands)
    return ee.batch.Export.image.toDrive(
        image=image,
        description=scene.scene_id,
        folder=config.DRIVE_FOLDER,
        fileNamePrefix=scene.scene_id,
        region=geometry,
        scale=scene.scale_meters,
        crs=scene.crs,
        fileFormat=config.EXPORT_FORMAT,
        formatOptions={"cloudOptimized": config.CLOUD_OPTIMIZED},
    )


def start_export(ee, task) -> str:
    """Start an export task and return its id."""
    task.start()
    return task.id
