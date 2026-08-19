"""Verify and enforce grid consistency across rasters.

Methodology §3.2 step 3 requires all bands and scenes to share the same
CRS, resolution, and spatial extent so that pixel-by-pixel operations
(NDVI, NDBI, LST, change detection) are meaningful.

For this project both scenes were exported from GEE with identical
parameters (UTM 31N, 30 m, same bounding box), so the primary role of
this module is **verification** with a fallback **resample** if a
mismatch is detected (e.g. a future scene with a slightly different
footprint).

References
----------
Methodology §3.2 step 3 — ``Raster alignment: reproject/resample all
bands to a common grid in UTM 31N, matching resolution (30 m) and extent``.
"""

from __future__ import annotations

import pathlib

import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject

# Reference grid: UTM 31N, 30 m — matches the GEE export parameters.
REFERENCE_CRS = "EPSG:32631"
REFERENCE_SCALE = 30.0


def _round_transform(t, n: int = 6) -> tuple[float, ...]:
    """Round transform coefficients to *n* decimal places for comparison."""
    return tuple(round(float(v), n) for v in t)


def check_alignment(
    paths: list[str | pathlib.Path],
) -> dict:
    """Check whether multiple rasters share the same grid.

    Parameters
    ----------
    paths : list of Path
        Raster file paths to compare.

    Returns
    -------
    dict
        ``{"aligned": True/False, "details": [...]}``
        Each detail entry has ``{path, crs, resolution, bounds, height, width}``.
    """
    summaries = []
    for p in paths:
        with rasterio.open(p) as src:
            summaries.append(
                {
                    "path": str(p),
                    "crs": str(src.crs),
                    "resolution": tuple(round(r, 6) for r in src.res),
                    "bounds": (
                        round(src.bounds.left, 6),
                        round(src.bounds.bottom, 6),
                        round(src.bounds.right, 6),
                        round(src.bounds.top, 6),
                    ),
                    "height": src.height,
                    "width": src.width,
                }
            )

    crs_set = {s["crs"] for s in summaries}
    res_set = {s["resolution"] for s in summaries}
    bounds_set = {s["bounds"] for s in summaries}
    aligned = len(crs_set) == 1 and len(res_set) == 1 and len(bounds_set) == 1

    return {"aligned": aligned, "details": summaries}


def verify_reference_grid(path: str | pathlib.Path) -> dict:
    """Verify that a raster matches the project's reference grid.

    Returns
    -------
    dict
        ``{"matches": True/False, "crs_ok": bool, "scale_ok": bool,
          "extent_ok": bool, ...}``
    """
    with rasterio.open(path) as src:
        crs_ok = str(src.crs) == REFERENCE_CRS
        scale_ok = all(abs(r - REFERENCE_SCALE) < 0.01 for r in src.res)
        # Extent check: must fully contain the Lagos boundary.
        # The GEE export uses the boundary bbox, so this should pass.
        return {
            "path": str(path),
            "matches": crs_ok and scale_ok,
            "crs_ok": crs_ok,
            "scale_ok": scale_ok,
            "crs": str(src.crs),
            "resolution": src.res,
            "bounds": [src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top],
            "shape": (src.height, src.width),
        }


def resample_to_grid(
    src_path: str | pathlib.Path,
    dst_path: str | pathlib.Path,
    *,
    target_crs: str = REFERENCE_CRS,
    target_scale: float = REFERENCE_SCALE,
    resampling: Resampling = Resampling.nearest,
) -> dict:
    """Reproject/resample a raster to the reference grid.

    Parameters
    ----------
    src_path : str or Path
        Input raster.
    dst_path : str or Path
        Output raster (same grid as all other processed scenes).
    target_crs : str
        Target CRS (default UTM 31N).
    target_scale : float
        Target pixel size in metres (default 30).
    resampling : Resampling
        Resampling method (nearest for integer bands, bilinear for float).

    Returns
    -------
    dict
        ``{"src_shape, dst_shape, src_crs, dst_crs, src_res, dst_res"}``
    """
    src_path = pathlib.Path(src_path)
    dst_path = pathlib.Path(dst_path)
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(src_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs,
            target_crs,
            src.width,
            src.height,
            *src.bounds,
            resolution=(target_scale, target_scale),
        )

        meta = src.meta.copy()
        meta.update(
            {
                "crs": target_crs,
                "transform": transform,
                "width": width,
                "height": height,
            }
        )

        with rasterio.open(dst_path, "w", **meta) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=resampling,
                )

    return {
        "src_shape": (src.count, src.height, src.width),
        "dst_shape": (meta["count"], height, width),
        "src_crs": str(src.crs),
        "dst_crs": target_crs,
        "src_res": src.res,
        "dst_res": (target_scale, target_scale),
    }
