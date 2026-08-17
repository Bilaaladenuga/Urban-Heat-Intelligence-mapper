"""Acquisition pipeline CLI (Phase 3 — Task 3.1).

Reproducible workflow: search Landsat 8/9 C2 L2 for each seasonal window
within the study area, select the best scene (with documented cloud
fallback), export it as a cloud-optimized GeoTIFF to Google Drive, and
record full metadata locally.

Usage:
    python -m remote_sensing.acquisition.pipeline --dry-run --year 2023
    python -m remote_sensing.acquisition.pipeline --year 2023

``--dry-run`` prints the full plan without touching Earth Engine, so the
workflow is inspectable before any credentials are involved.

Authentication (one-time, live mode only):
    python -m earthengine authenticate
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from . import config, metadata
from .export import build_export_task, start_export
from .models import SceneRecord
from .search import plan_window, window_date_range

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("acquisition")


def load_geometry_geojson() -> dict:
    """Load the study-area boundary GeoJSON (Phase 2 output)."""
    if not config.GEOMETRY_SOURCE.exists():
        raise FileNotFoundError(
            f"Boundary GeoJSON not found: {config.GEOMETRY_SOURCE}. "
            "Run scripts/fetch_lagos_boundary.py first (Task 2.1)."
        )
    return json.loads(config.GEOMETRY_SOURCE.read_text(encoding="utf-8"))


def plan(
    ee,
    *,
    year: int,
    cloud_threshold_pct: float,
    geometry_geojson: dict,
) -> list[SceneRecord | None]:
    """Search/select every seasonal window (no exports)."""
    geometry = ee.Geometry(geometry_geojson)
    records: list[SceneRecord | None] = []
    for window in config.SEASONAL_WINDOWS:
        record, messages = plan_window(
            ee,
            geometry=geometry,
            window=window,
            year=year,
            cloud_threshold_pct=cloud_threshold_pct,
        )
        for message in messages:
            logger.info(message)
        records.append(record)
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2023,
                        help="analysis year for the seasonal windows")
    parser.add_argument("--cloud-threshold", type=float,
                        default=config.CLOUD_THRESHOLD_PCT,
                        help="cloud-cover ceiling in percent (default: "
                             f"{config.CLOUD_THRESHOLD_PCT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the plan without calling Earth Engine")
    args = parser.parse_args(argv)

    if args.dry_run:
        print_dry_run(args.year, args.cloud_threshold)
        return 0

    try:
        import ee
    except ImportError:
        logger.error(
            "earthengine-api is not installed. Install with:\n"
            "    pip install earthengine-api\n"
            "then authenticate once:\n"
            "    python -m earthengine authenticate"
        )
        return 1
    try:
        ee.Initialize()
    except Exception as exc:  # noqa: BLE001 - auth errors surface to the user
        logger.error("Earth Engine initialization failed: %s", exc)
        logger.error("Authenticate once with: python -m earthengine authenticate")
        return 1

    geojson = load_geometry_geojson()
    logger.info("Searching scenes (year=%s, cloud<=%s%%) ...",
                args.year, args.cloud_threshold)
    records = plan(
        ee,
        year=args.year,
        cloud_threshold_pct=args.cloud_threshold,
        geometry_geojson=geojson,
    )
    selected = [r for r in records if r is not None]

    if not selected:
        logger.warning("No scenes selected in any window — nothing to export.")
        return 0

    geometry = ee.Geometry(geojson)
    for record in selected:
        record.geometry_source = str(config.GEOMETRY_SOURCE)
        task = build_export_task(ee, scene=record, geometry=geometry)
        task_id = start_export(ee, task)
        record.extra["export_task_id"] = task_id
        metadata.save_record(record)
        logger.info("Exported %s -> Drive folder '%s' (task %s)",
                    record.scene_id, config.DRIVE_FOLDER, task_id)

    metadata.update_manifest(selected)
    logger.info("Metadata written to %s", config.MANIFEST_FILE)
    return 0


def print_dry_run(year: int, cloud_threshold_pct: float) -> None:
    """Print the acquisition plan without touching Earth Engine."""
    geojson = load_geometry_geojson()
    bounds = _geojson_bounds(geojson)
    print("=" * 72)
    print("ACQUISITION PLAN (dry run — no Earth Engine calls)")
    print("=" * 72)
    print(f"Collections   : {', '.join(config.COLLECTIONS)}")
    print(f"WRS path/row  : {config.WRS_PATH}/{config.WRS_ROW}")
    print(f"Cloud ceiling : {cloud_threshold_pct}% "
          f"(default {config.CLOUD_THRESHOLD_PCT}%)")
    print(f"Analysis year : {year}")
    print(f"Geometry      : {config.GEOMETRY_SOURCE} (bbox {bounds})")
    print(f"Bands         : {', '.join(config.BANDS)}")
    print(f"Export        : {config.SCALE_METERS} m, {config.EXPORT_CRS}, "
          f"{config.EXPORT_FORMAT} (cloud-optimized: "
          f"{config.CLOUD_OPTIMIZED}) -> Drive folder "
          f"'{config.DRIVE_FOLDER}'")
    print(f"Metadata      : {config.IMAGERY_DIR} (gitignored)")
    print("-" * 72)
    for window in config.SEASONAL_WINDOWS:
        start, end = window_date_range(window, year)
        print(f"{window:<5}: {start} .. {end}  ->  best scene by cloud "
              f"cover <= {cloud_threshold_pct}% (fallback: lowest cloud, "
              "deviation recorded)")
    print("=" * 72)
    print("Live run needs one-time auth:  python -m earthengine authenticate")


def _geojson_bounds(geojson: dict) -> str:
    """Crude bbox of the boundary feature (lon/lat) for the dry-run print."""
    feature = geojson["features"][0]
    geometry = feature.get("geometry", {})
    coords = geometry.get("coordinates", [])
    xs: list[float] = []
    ys: list[float] = []
    stack = list(coords)
    while stack:
        item = stack.pop()
        if isinstance(item, list) and item and isinstance(item[0], (int, float)):
            if len(item) >= 2:
                xs.append(item[0])
                ys.append(item[1])
        elif isinstance(item, list):
            stack.extend(item)
    if not xs:
        return "unknown"
    return (f"lon {min(xs):.4f}..{max(xs):.4f}, "
            f"lat {min(ys):.4f}..{max(ys):.4f}")


if __name__ == "__main__":
    sys.exit(main())
