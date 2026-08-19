"""Preprocessing pipeline — orchestrates the full Phase 4 workflow.

Usage::

    # Process all scenes (dry + wet) for a given year:
    python -m remote_sensing.preprocessing.pipeline --year 2023

    # Process a single scene:
    python -m remote_sensing.preprocessing.pipeline --scene LC09_191055_20221219

    # Dry run (no output files):
    python -m remote_sensing.preprocessing.pipeline --year 2023 --dry-run

Pipeline steps (per methodology §3.2):

    1. Cloud masking  (QA_PIXEL bit flags)
    2. Clipping       (Lagos State boundary)
    3. Alignment      (verify / enforce UTM 31N, 30 m grid)
    4. Nodata handling (explicit nodata = 0, validation)

Input:  data/raw/imagery/{scene_id}/{scene_id}.tif  (6 bands)
Output: data/processed/imagery/{scene_id}/{scene_id}_processed.tif
"""

from __future__ import annotations

import json
import pathlib
import time

import numpy as np
import rasterio

from remote_sensing.acquisition.config import GEOMETRY_SOURCE
from remote_sensing.preprocessing.align import (
    check_alignment,
    verify_reference_grid,
)
from remote_sensing.preprocessing.clip import clip_raster, load_boundary
from remote_sensing.preprocessing.cloud_mask import (
    apply_cloud_mask,
    valid_pixel_fraction,
)
from remote_sensing.preprocessing.nodata import (
    nodata_summary,
    validate_all_bands,
)

# --- Paths ---
ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "imagery"
PROCESSED_DIR = ROOT / "data" / "processed" / "imagery"

# Band names matching the GEE export order (1-indexed).
BAND_NAMES = ["SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10", "QA_PIXEL"]


def _find_scenes(year: int | None = None) -> list[pathlib.Path]:
    """Discover scene folders under data/raw/imagery/."""
    if not RAW_DIR.exists():
        return []
    scenes = sorted(
        p for p in RAW_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )
    if year is not None:
        scenes = [s for s in scenes if str(year) in s.name]
    return scenes


def process_scene(
    scene_dir: pathlib.Path,
    *,
    dry_run: bool = False,
) -> dict:
    """Run the full preprocessing pipeline on one scene.

    Parameters
    ----------
    scene_dir : Path
        Directory containing ``{scene_id}.tif``.
    dry_run : bool
        If True, perform all validation but do not write output files.

    Returns
    -------
    dict
        Full processing record (steps, validation, timing).
    """
    scene_id = scene_dir.name
    src_path = scene_dir / f"{scene_id}.tif"
    dst_dir = PROCESSED_DIR / scene_id
    dst_path = dst_dir / f"{scene_id}_processed.tif"
    record: dict = {
        "scene_id": scene_id,
        "src_path": str(src_path),
        "dst_path": str(dst_path),
        "steps": {},
        "validation": {},
        "timing": {},
    }

    t0 = time.perf_counter()

    # --- Step 0: Verify reference grid ---
    grid = verify_reference_grid(src_path)
    record["steps"]["0_grid_check"] = grid
    if not grid["matches"]:
        print(f"  WARNING: {scene_id} does not match reference grid — resample needed")
        record["steps"]["0_grid_check"]["action"] = "needs_resample"
    else:
        record["steps"]["0_grid_check"]["action"] = "ok"

    # --- Step 1: Cloud masking ---
    t1 = time.perf_counter()
    with rasterio.open(src_path) as src:
        bands_raw: dict[str, np.ndarray] = {}
        for i, name in enumerate(BAND_NAMES, 1):
            bands_raw[name] = src.read(i)

    valid_mask, masked_bands = apply_cloud_mask(bands_raw)
    vpf = valid_pixel_fraction(valid_mask)
    record["steps"]["1_cloud_mask"] = {
        "valid_pixel_fraction": round(vpf, 4),
        "total_pixels": valid_mask.size,
        "valid_pixels": int(valid_mask.sum()),
    }
    print(f"  Cloud mask: {vpf * 100:.1f}% valid pixels")
    record["timing"]["cloud_mask_s"] = round(time.perf_counter() - t1, 3)

    # --- Step 2: Clipping ---
    t2 = time.perf_counter()
    geometries = load_boundary(GEOMETRY_SOURCE, target_crs=grid["crs"])

    # Write masked bands temporarily for clipping.
    tmp_masked_path = dst_dir / f"{scene_id}_masked.tif"
    if not dry_run:
        dst_dir.mkdir(parents=True, exist_ok=True)
        with rasterio.open(src_path) as src:
            meta = src.meta.copy()
            meta.update({"count": len(BAND_NAMES), "nodata": 0})
            with rasterio.open(tmp_masked_path, "w", **meta) as tmp:
                for i, name in enumerate(BAND_NAMES, 1):
                    if name in masked_bands:
                        tmp.write(masked_bands[name], i)
                    else:
                        # QA_PIXEL is not in masked_bands — keep it unmasked
                        # for reference, but mark masked pixels as 0.
                        qa = bands_raw[name].copy()
                        qa[~valid_mask] = 0
                        tmp.write(qa, i)

        clip_meta = clip_raster(tmp_masked_path, geometries, dst_path, nodata=0)
        record["steps"]["2_clip"] = clip_meta
        print(f"  Clip: {clip_meta['pixels_removed']:,} pixels removed")
        tmp_masked_path.unlink(missing_ok=True)
    else:
        record["steps"]["2_clip"] = {"dry_run": True, "geometries_loaded": len(geometries)}

    record["timing"]["clip_s"] = round(time.perf_counter() - t2, 3)

    # --- Step 3: Alignment verification (on output) ---
    t3 = time.perf_counter()
    if not dry_run and dst_path.exists():
        alignment = check_alignment([src_path, dst_path])
        record["steps"]["3_alignment"] = alignment
        if alignment["aligned"]:
            print("  Alignment: src and dst share identical grid [OK]")
        else:
            print("  WARNING: grid mismatch after clipping")
    else:
        record["steps"]["3_alignment"] = {"dry_run": True}
    record["timing"]["alignment_s"] = round(time.perf_counter() - t3, 3)

    # --- Step 4: Nodata validation ---
    t4 = time.perf_counter()
    if not dry_run and dst_path.exists():
        with rasterio.open(dst_path) as dst:
            out_bands = {BAND_NAMES[i]: dst.read(i + 1) for i in range(len(BAND_NAMES))}
        validation = validate_all_bands(out_bands)
        summary = nodata_summary(valid_mask)
        record["validation"] = {"bands": validation, "nodata_summary": summary}
        all_ok = all(v["in_range"] for v in validation)
        print(f"  Nodata: {summary['valid_pct']:.1f}% valid -- {'all bands in range' if all_ok else 'range issues'}")
    else:
        record["validation"] = {"dry_run": True}
    record["timing"]["nodata_s"] = round(time.perf_counter() - t4, 3)

    record["timing"]["total_s"] = round(time.perf_counter() - t0, 3)
    return record


def run_pipeline(
    *,
    year: int | None = None,
    scene_id: str | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """Run preprocessing on one or all scenes.

    Parameters
    ----------
    year : int, optional
        Process all scenes containing this year in their folder name.
    scene_id : str, optional
        Process a single scene by exact folder name.
    dry_run : bool
        Validate only — no output files written.

    Returns
    -------
    list of dict
        Processing records for each scene.
    """
    if scene_id:
        if isinstance(scene_id, str):
            scenes = [RAW_DIR / scene_id]
        else:
            scenes = [RAW_DIR / s for s in scene_id]
    else:
        scenes = _find_scenes(year)

    if not scenes:
        print("No scenes found.")
        return []

    print(f"Preprocessing {len(scenes)} scene(s) — dry_run={dry_run}")
    records = []
    for scene_dir in scenes:
        if not scene_dir.is_dir():
            print(f"  SKIP: {scene_dir} is not a directory")
            continue
        print(f"\nProcessing: {scene_dir.name}")
        record = process_scene(scene_dir, dry_run=dry_run)
        records.append(record)

    return records


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Landsat preprocessing pipeline (Phase 4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--year", type=int, help="Process all scenes for this year")
    parser.add_argument("--scene", type=str, nargs="+", help="Process one or more scenes by ID")
    parser.add_argument("--dry-run", action="store_true", help="Validate only")
    args = parser.parse_args()

    if not args.year and not args.scene:
        # Process all scenes
        args.all = True
    else:
        args.all = False

    records = run_pipeline(
        year=args.year,
        scene_id=args.scene,
        dry_run=args.dry_run,
    )

    if records:
        # Write manifest.
        manifest_path = PROCESSED_DIR / "preprocessing_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w") as f:
            json.dump(records, f, indent=2, default=str)
        print(f"\nManifest written: {manifest_path}")


if __name__ == "__main__":
    main()
