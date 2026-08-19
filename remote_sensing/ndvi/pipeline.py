"""NDVI pipeline — computes NDVI from preprocessed Landsat scenes.

Usage::

    # Compute NDVI for all preprocessed scenes:
    python -m remote_sensing.ndvi.pipeline

    # Compute for a specific scene:
    python -m remote_sensing.ndvi.pipeline --scene LC09_191055_20221219

    # Dry run (validate only):
    python -m remote_sensing.ndvi.pipeline --scene LC09_191055_20221219 --dry-run

Output: data/processed/ndvi/{scene_id}_ndvi.tif
"""

from __future__ import annotations

import json
import pathlib
import time

from remote_sensing.ndvi.compute import (
    compute_ndvi,
    compute_stats,
    ndvi_from_scene,
    validate_ndvi,
)

# --- Paths ---
ROOT = pathlib.Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed" / "imagery"
NDVI_DIR = ROOT / "data" / "processed" / "ndvi"


def _find_scenes(year: int | None = None) -> list[pathlib.Path]:
    """Discover preprocessed scene folders."""
    if not PROCESSED_DIR.exists():
        return []
    scenes = []
    for p in sorted(PROCESSED_DIR.iterdir()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        tif = p / f"{p.name}_processed.tif"
        if tif.exists():
            scenes.append(p)
    if year is not None:
        scenes = [s for s in scenes if str(year) in s.name]
    return scenes


def process_scene(scene_dir: pathlib.Path, *, dry_run: bool = False) -> dict:
    """Compute NDVI for a single scene.

    Parameters
    ----------
    scene_dir : Path
        Directory containing {scene_id}_processed.tif.
    dry_run : bool
        If True, validate only — no output files written.

    Returns
    -------
    dict
        Processing record with validation results.
    """
    scene_id = scene_dir.name
    src_path = scene_dir / f"{scene_id}_processed.tif"
    dst_path = NDVI_DIR / scene_id / f"{scene_id}_ndvi.tif"
    record: dict = {
        "scene_id": scene_id,
        "src_path": str(src_path),
        "dst_path": str(dst_path),
        "steps": {},
        "timing": {},
    }

    t0 = time.perf_counter()

    if dry_run:
        # Read bands and compute NDVI in memory (no write).
        import rasterio

        with rasterio.open(src_path) as src:
            red = src.read(1)
            nir = src.read(2)

        ndvi = compute_ndvi(red, nir)
        stats = compute_stats(ndvi)
        validation = validate_ndvi(ndvi)
        record["steps"]["ndvi"] = {"dry_run": True, "stats": stats}
        record["steps"]["validation"] = validation
    else:
        result = ndvi_from_scene(src_path, dst_path)
        record["steps"]["ndvi"] = result["stats"]

        # Validate the output.
        import rasterio

        with rasterio.open(dst_path) as src:
            ndvi = src.read(1)
        validation = validate_ndvi(ndvi)
        record["steps"]["validation"] = validation

    record["timing"]["total_s"] = round(time.perf_counter() - t0, 3)
    return record


def run_pipeline(
    *,
    year: int | None = None,
    scene_id: str | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """Run NDVI computation on one or all preprocessed scenes."""
    if scene_id:
        scenes = [PROCESSED_DIR / scene_id]
    else:
        scenes = _find_scenes(year)

    if not scenes:
        print("No preprocessed scenes found.")
        return []

    print(f"Computing NDVI for {len(scenes)} scene(s) — dry_run={dry_run}")
    records = []
    for scene_dir in scenes:
        if not scene_dir.is_dir():
            print(f"  SKIP: {scene_dir} is not a directory")
            continue
        print(f"\nProcessing: {scene_dir.name}")
        record = process_scene(scene_dir, dry_run=dry_run)
        records.append(record)

        # Print summary.
        stats = record["steps"]["ndvi"]
        if "mean" in stats:
            print(f"  NDVI: mean={stats['mean']:.4f}, range=[{stats['min']:.4f}, {stats['max']:.4f}]")
            print(f"  Valid: {stats['valid_pct']:.1f}% ({stats['valid_pixels']:,} pixels)")
        validation = record["steps"]["validation"]
        if validation.get("notes"):
            for note in validation["notes"]:
                print(f"  Validation: {note}")

    return records


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="NDVI computation pipeline (Phase 5)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--year", type=int, help="Process scenes for this year")
    parser.add_argument("--scene", type=str, help="Process a single scene by ID")
    parser.add_argument("--dry-run", action="store_true", help="Validate only")
    args = parser.parse_args()

    records = run_pipeline(
        year=args.year,
        scene_id=args.scene,
        dry_run=args.dry_run,
    )

    if records:
        manifest_path = NDVI_DIR / "ndvi_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w") as f:
            json.dump(records, f, indent=2, default=str)
        print(f"\nManifest written: {manifest_path}")


if __name__ == "__main__":
    main()
