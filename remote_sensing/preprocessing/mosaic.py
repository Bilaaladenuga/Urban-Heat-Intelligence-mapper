"""
Mosaic two overlapping Landsat scenes into a single raster.

The existing scene (LC09_191055_20221219) covers most of Lagos but has
gaps at the west and east edges. The second scene (LC09_190055_20221228)
extends further west and east, filling those gaps.

The mosaic is done BEFORE cloud masking — both raw scenes are mosaicked
into a single multi-band raster, then the standard preprocessing pipeline
is applied to the result.

Output:
    data/raw/imagery/LC09_191055_190055_mosaic/LC09_191055_190055_mosaic.tif
"""

from __future__ import annotations

import pathlib
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject, calculate_default_transform

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "imagery"

# Scene paths.
SCENE_A = RAW_DIR / "LC09_191055_20221219" / "LC09_191055_20221219.tif"
SCENE_B = RAW_DIR / "LC09_190055_20221228" / "LC09_190055_20221228.tif"
OUTPUT_DIR = RAW_DIR / "LC09_191055_190055_mosaic"
OUTPUT_FILE = OUTPUT_DIR / "LC09_191055_190055_mosaic.tif"

# Band names (matching the input rasters).
BAND_NAMES = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10", "QA_PIXEL"]


def mosaic_scenes(scene_a: pathlib.Path, scene_b: pathlib.Path, output: pathlib.Path) -> dict:
    """Mosaic two overlapping scenes into a single raster.
    
    Strategy: compute the union bounding box, create an empty output grid,
    then reproject each scene into the output grid. Where both scenes have
    data, scene A (the primary) takes priority; scene B fills the gaps.
    
    Returns a dict with stats about the mosaic.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with rasterio.open(scene_a) as src_a, rasterio.open(scene_b) as src_b:
        # Verify compatibility.
        assert src_a.crs == src_b.crs, f"CRS mismatch: {src_a.crs} vs {src_b.crs}"
        assert src_a.dtypes[0] == src_b.dtypes[0], f"Dtype mismatch: {src_a.dtypes[0]} vs {src_b.dtypes[0]}"
        
        dtype = src_a.dtypes[0]
        crs = src_a.crs
        
        # Build band name maps.
        names_a = {src_a.descriptions[i]: i + 1 for i in range(src_a.count) if src_a.descriptions[i]}
        names_b = {src_b.descriptions[i]: i + 1 for i in range(src_b.count) if src_b.descriptions[i]}
        
        # Output bands = all bands from scene B (the more complete one).
        out_band_names = [src_b.descriptions[i] for i in range(src_b.count) if src_b.descriptions[i]]
        n_bands = len(out_band_names)
        
        print(f"Scene A bands: {list(names_a.keys())}")
        print(f"Scene B bands: {list(names_b.keys())}")
        print(f"Output bands:  {out_band_names}")
        
        # Compute union bounds.
        bounds_a = src_a.bounds
        bounds_b = src_b.bounds
        union_left = min(bounds_a.left, bounds_b.left)
        union_bottom = min(bounds_a.bottom, bounds_b.bottom)
        union_right = max(bounds_a.right, bounds_b.right)
        union_top = max(bounds_a.top, bounds_b.top)
        
        pixel_size = 30.0  # meters (Landsat native resolution)
        out_width = int(np.ceil((union_right - union_left) / pixel_size))
        out_height = int(np.ceil((union_top - union_bottom) / pixel_size))
        out_transform = from_bounds(union_left, union_bottom, union_right, union_top, out_width, out_height)
        
        print(f"Mosaic output: {out_width}x{out_height} pixels ({out_width*pixel_size/1000:.1f} x {out_height*pixel_size/1000:.1f} km)")
        print(f"Bounds: L={union_left:.0f} B={union_bottom:.0f} R={union_right:.0f} T={union_top:.0f}")
        
        # Initialize output.
        mosaic = np.zeros((n_bands, out_height, out_width), dtype=dtype)
        
        # Reproject scene A (primary) for overlapping bands.
        print("Reprojecting Scene A (LC09_191055_20221219)...")
        for out_idx, band_name in enumerate(out_band_names):
            if band_name in names_a:
                src_band_idx = names_a[band_name]
                reproject(
                    source=rasterio.band(src_a, src_band_idx),
                    destination=mosaic[out_idx],
                    src_transform=src_a.transform,
                    src_crs=src_a.crs,
                    dst_transform=out_transform,
                    dst_crs=crs,
                    resampling=Resampling.nearest,
                )
            # Bands not in scene A stay as zeros (scene B will fill them).
        
        # Mark valid pixels from scene A (using band 1 as reference).
        if dtype == np.uint16:
            coverage = mosaic[0] > 0
        else:
            coverage = ~np.isnan(mosaic[0])
        valid_a = np.sum(coverage)
        print(f"  Scene A valid pixels: {valid_a} ({100*valid_a/(out_width*out_height):.1f}%)")
        
        # Reproject scene B (secondary) — fill gaps + provide missing bands.
        print("Reprojecting Scene B (LC09_190055_20221228)...")
        temp = np.zeros((n_bands, out_height, out_width), dtype=dtype)
        for out_idx, band_name in enumerate(out_band_names):
            if band_name in names_b:
                src_band_idx = names_b[band_name]
                reproject(
                    source=rasterio.band(src_b, src_band_idx),
                    destination=temp[out_idx],
                    src_transform=src_b.transform,
                    src_crs=src_b.crs,
                    dst_transform=out_transform,
                    dst_crs=crs,
                    resampling=Resampling.nearest,
                )
        
        # Fill gaps: where mosaic is 0 but temp has data.
        if dtype == np.uint16:
            gap_mask = (mosaic[0] == 0) & (temp[0] > 0)
        else:
            gap_mask = np.isnan(mosaic[0]) & ~np.isnan(temp[0])
        
        for band_idx in range(n_bands):
            mosaic[band_idx][gap_mask] = temp[band_idx][gap_mask]
        
        # For bands only in scene B (e.g. SR_B2, SR_B3), copy directly.
        for out_idx, band_name in enumerate(out_band_names):
            if band_name not in names_a and band_name in names_b:
                mosaic[out_idx] = temp[out_idx]
                print(f"  Band {band_name}: scene B only (copied directly)")
        
        coverage_final = mosaic[0] > 0 if dtype == np.uint16 else ~np.isnan(mosaic[0])
        valid_total = np.sum(coverage_final)
        filled_by_b = np.sum(gap_mask)
        
        print(f"  Scene B filled {filled_by_b} gap pixels ({100*filled_by_b/(out_width*out_height):.1f}%)")
        print(f"  Final valid pixels: {valid_total} ({100*valid_total/(out_width*out_height):.1f}%)")
    
    # Write output.
    profile = {
        "driver": "GTiff",
        "width": out_width,
        "height": out_height,
        "count": n_bands,
        "dtype": dtype,
        "crs": crs,
        "transform": out_transform,
        "nodata": 0,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    
    with rasterio.open(output, "w", **profile) as dst:
        for band_idx in range(n_bands):
            dst.write(mosaic[band_idx], band_idx + 1)
            dst.set_band_description(band_idx + 1, out_band_names[band_idx])
    
    print(f"\nMosaic written: {output}")
    print(f"Size: {output.stat().st_size / 1024 / 1024:.1f} MB")
    
    return {
        "output": str(output),
        "width": out_width,
        "height": out_height,
        "valid_pixels": int(valid_total),
        "total_pixels": out_width * out_height,
        "gap_filled": int(filled_by_b),
    }


if __name__ == "__main__":
    print("=" * 60)
    print("MOSAICKING TWO LANDSAT SCENES")
    print("=" * 60)
    print(f"Scene A: {SCENE_A.name}")
    print(f"Scene B: {SCENE_B.name}")
    print(f"Output:  {OUTPUT_FILE}")
    print()
    
    if not SCENE_A.exists():
        print(f"ERROR: Scene A not found: {SCENE_A}")
    elif not SCENE_B.exists():
        print(f"ERROR: Scene B not found: {SCENE_B}")
    else:
        stats = mosaic_scenes(SCENE_A, SCENE_B, OUTPUT_FILE)
        print()
        print("=" * 60)
        print("MOSAIC COMPLETE")
        print("=" * 60)
