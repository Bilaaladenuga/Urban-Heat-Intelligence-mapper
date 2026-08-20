"""NDVI computation from preprocessed Landsat Collection 2 Level-2 scenes.

Equation (Rouse et al. 1974)::

    NDVI = (NIR − RED) / (NIR + RED)

Bands (Landsat 8/9 C2 L2):
    RED = SR_B4 (band 1 in the preprocessed raster)
    NIR = SR_B5 (band 2 in the preprocessed raster)

C2 L2 scaling (USGS conventions)::

    reflectance = raw_value × 0.0000275 − 0.2

Output: float32 NDVI raster in [−1, 1] (with nodata = NaN).

References
----------
Methodology §3.3 — NDVI (Phase 5).
Rouse et al. (1974) — NDVI definition.
USGS (2023) — Landsat C2 L2 surface reflectance scaling.
"""

from __future__ import annotations

import pathlib

import numpy as np
import rasterio
from numpy.typing import NDArray

# C2 L2 surface reflectance scaling constants (USGS).
SCALE_FACTOR = 0.0000275
ADD_OFFSET = -0.2

# Band indices (1-indexed) in the preprocessed raster.
BAND_RED = 1  # SR_B4
BAND_NIR = 2  # SR_B5

# Output dtype.
NDVI_DTYPE = np.float32


def reflectance(raw: NDArray[np.uint16]) -> NDArray[np.float64]:
    """Apply C2 L2 scaling to convert raw uint16 to reflectance.

    Parameters
    ----------
    raw : ndarray of uint16
        Raw surface reflectance band values.

    Returns
    -------
    ndarray of float64
        Surface reflectance values (typically 0–1, but can exceed 1 for
        bright surfaces).
    """
    return raw.astype(np.float64) * SCALE_FACTOR + ADD_OFFSET


def compute_ndvi(
    red: NDArray[np.uint16],
    nir: NDArray[np.uint16],
    *,
    nodata: int = 0,
) -> NDArray[np.float32]:
    """Compute NDVI from raw RED and NIR bands.

    Parameters
    ----------
    red : ndarray of uint16
        SR_B4 (Red) band — raw, pre-scaled values.
    nir : ndarray of uint16
        SR_B5 (NIR) band — raw, pre-scaled values.
    nodata : int
        Value indicating no-data pixels (default 0).

    Returns
    -------
    ndarray of float32
        NDVI values in [−1, 1].  Nodata pixels are set to ``np.nan``.

    Notes
    -----
    - Nodata pixels (raw value == 0 in either band) are set to NaN.
    - Pixels below the USGS valid reflectance range (< 7273 raw,
      which maps to < 0.0 scaled) are excluded — these are fill or
      degraded values that produce unreliable NDVI.
    - Pixels where the denominator is very small (< 0.001) are set to
      NaN to avoid extreme values from near-zero division.
    """
    red_ref = reflectance(red)
    nir_ref = reflectance(nir)

    # USGS valid range: raw >= 7273 maps to reflectance >= 0.0.
    # Pixels below this are fill or degraded and should be excluded.
    USGS_VALID_MIN = 7273

    # Build the valid-pixel mask.
    valid = (
        (red != nodata)
        & (nir != nodata)
        & (red >= USGS_VALID_MIN)
        & (nir >= USGS_VALID_MIN)
    )

    # Compute NDVI.
    denominator = nir_ref + red_ref
    ndvi = np.full(red.shape, np.nan, dtype=NDVI_DTYPE)

    # Avoid division by zero or near-zero denominators.
    MIN_DENOMINATOR = 0.001
    compute_mask = valid & (np.abs(denominator) >= MIN_DENOMINATOR)
    ndvi[compute_mask] = (
        (nir_ref[compute_mask] - red_ref[compute_mask]) / denominator[compute_mask]
    ).astype(NDVI_DTYPE)

    return ndvi


def ndvi_from_scene(
    scene_path: str | pathlib.Path,
    output_path: str | pathlib.Path,
    *,
    nodata: int = 0,
) -> dict:
    """Compute NDVI from a preprocessed scene and write the result.

    Parameters
    ----------
    scene_path : str or Path
        Path to the preprocessed GeoTIFF (6 bands).
    output_path : str or Path
        Path for the output NDVI raster (float32, single band).
    nodata : int
        Nodata value in the input raster.

    Returns
    -------
    dict
        Metadata about the computation: ``{scene_id, output_path, stats}``.
    """
    scene_path = pathlib.Path(scene_path)
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(scene_path) as src:
        # Read bands by name from raster metadata (handles any band count/ordering).
        band_map = {}
        for i in range(src.count):
            desc = src.descriptions[i] if src.descriptions[i] else f"BAND_{i+1}"
            band_map[desc] = i + 1
        red = src.read(band_map["SR_B4"])
        nir = src.read(band_map["SR_B5"])

        ndvi = compute_ndvi(red, nir, nodata=nodata)

        # Write output.
        meta = src.meta.copy()
        meta.update(
            {
                "count": 1,
                "dtype": "float32",
                "nodata": np.nan,
                "compress": "deflate",
            }
        )
        # Remove band descriptions from the copy.
        meta.pop("descriptions", None)

        with rasterio.open(output_path, "w", **meta) as dst:
            dst.write(ndvi, 1)
            dst.set_band_description(1, "NDVI")

    stats = compute_stats(ndvi)
    return {
        "scene_id": scene_path.stem.replace("_processed", ""),
        "output_path": str(output_path),
        "stats": stats,
    }


def compute_stats(ndvi: NDArray[np.float32]) -> dict:
    """Compute descriptive statistics for an NDVI array.

    Parameters
    ----------
    ndvi : ndarray of float32
        NDVI values (may contain NaN).

    Returns
    -------
    dict
        ``{min, max, mean, median, std, p25, p75, valid_pixels, total_pixels,
          valid_pct, nan_count}``
    """
    valid = ndvi[~np.isnan(ndvi)]
    total = ndvi.size
    valid_count = valid.size

    if valid_count == 0:
        return {
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "p25": None,
            "p75": None,
            "valid_pixels": 0,
            "total_pixels": total,
            "valid_pct": 0.0,
            "nan_count": total,
        }

    return {
        "min": round(float(valid.min()), 4),
        "max": round(float(valid.max()), 4),
        "mean": round(float(valid.mean()), 4),
        "median": round(float(np.median(valid)), 4),
        "std": round(float(valid.std()), 4),
        "p25": round(float(np.percentile(valid, 25)), 4),
        "p75": round(float(np.percentile(valid, 75)), 4),
        "valid_pixels": int(valid_count),
        "total_pixels": total,
        "valid_pct": round(valid_count / total * 100, 2),
        "nan_count": int(total - valid_count),
    }


def validate_ndvi(ndvi: NDArray[np.float32]) -> dict:
    """Validate NDVI values against expected ranges.

    Checks per methodology §3.3 and §6 (QC checklist):
    - Range: all valid pixels within [−1, 1].
    - Land-cover expectations: water ≈ negative, dense veg ≈ 0.4–0.9,
      bare/urban ≈ ≤ 0.2.

    Returns
    -------
    dict
        ``{range_ok, min, max, out_of_range_count, water_pct, veg_pct,
          bare_urban_pct, notes}``
    """
    valid = ndvi[~np.isnan(ndvi)]
    if valid.size == 0:
        return {"range_ok": False, "notes": "No valid pixels"}

    vmin = float(valid.min())
    vmax = float(valid.max())
    out_of_range = int(((valid < -1) | (valid > 1)).sum())

    # Land-cover expectation bands (rough references, not thresholds).
    water_pct = float((valid < 0).sum() / valid.size * 100)
    veg_pct = float(((valid >= 0.4) & (valid <= 0.9)).sum() / valid.size * 100)
    bare_urban_pct = float((valid <= 0.2).sum() / valid.size * 100)

    notes = []
    if out_of_range > 0:
        notes.append(
            f"{out_of_range} pixels outside [-1, 1] "
            f"({out_of_range / valid.size * 100:.2f}%) -- likely bright surfaces "
            f"with reflectance > 1.0"
        )
    if water_pct > 30:
        notes.append(f"High water fraction ({water_pct:.1f}%) -- check cloud/shadow masking")
    if vmin < -1:
        notes.append(f"Minimum NDVI {vmin:.4f} is below -1 -- possible water or processing artifact")

    return {
        "range_ok": out_of_range == 0,
        "min": vmin,
        "max": vmax,
        "out_of_range_count": out_of_range,
        "out_of_range_pct": round(out_of_range / valid.size * 100, 2),
        "water_pct": round(water_pct, 2),
        "veg_pct": round(veg_pct, 2),
        "bare_urban_pct": round(bare_urban_pct, 2),
        "notes": notes if notes else ["All values within [-1, 1]"],
    }
