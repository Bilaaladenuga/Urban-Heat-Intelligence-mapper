"""Clip rasters to the Lagos State study-area boundary.

The clipping step reduces the scene footprint from the full Landsat swath
(rectangle) to the actual study-area polygon, which:

- Removes irrelevant pixels (ocean, neighbouring states).
- Reduces downstream processing time and storage.
- Produces clean, study-area-aligned outputs.

The boundary is loaded from the Phase 2 GeoJSON export
(``data/processed/boundaries/lagos_state.geojson``) and reprojected to the
raster CRS (UTM 31N) before masking.

References
----------
Methodology §3.2 step 2 — ``Clip to Lagos State AOI``.
"""

from __future__ import annotations

import pathlib

import geopandas as gpd
import rasterio
from rasterio.mask import mask as rio_mask
from shapely.geometry import mapping


def load_boundary(
    boundary_path: str | pathlib.Path,
    target_crs: str = "EPSG:32631",
) -> list[dict]:
    """Load the study-area boundary and reproject to the target CRS.

    Parameters
    ----------
    boundary_path : str or Path
        Path to the GeoJSON file containing the study-area polygon.
    target_crs : str
        CRS to reproject into (default UTM 31N to match Landsat rasters).

    Returns
    -------
    list of dict
        GeoJSON-style geometry features suitable for ``rasterio.mask.mask``.
    """
    gdf = gpd.read_file(boundary_path)
    if gdf.crs is None:
        raise ValueError(f"Boundary file has no CRS: {boundary_path}")
    if str(gdf.crs) != target_crs:
        gdf = gdf.to_crs(target_crs)
    return [mapping(geom) for geom in gdf.geometry]


def clip_raster(
    src_path: str | pathlib.Path,
    geometries: list[dict],
    dst_path: str | pathlib.Path,
    *,
    nodata: int = 0,
    compress: str = "deflate",
) -> dict:
    """Clip a raster to the given geometries and write the result.

    Parameters
    ----------
    src_path : str or Path
        Input raster (e.g. raw or cloud-masked GeoTIFF).
    geometries : list of dict
        GeoJSON geometry dicts (from :func:`load_boundary`).
    dst_path : str or Path
        Output clipped raster path.
    nodata : int
        Value to assign to pixels outside the boundary.
    compress : str
        Compression for the output file.

    Returns
    -------
    dict
        Metadata about the clipping operation:
        ``{src_shape, dst_shape, pixels_removed, nodata}``.
    """
    src_path = pathlib.Path(src_path)
    dst_path = pathlib.Path(dst_path)
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(src_path) as src:
        out_image, out_transform = rio_mask(
            src,
            geometries,
            crop=True,
            nodata=nodata,
            filled=True,
        )

        out_meta = src.meta.copy()
        out_meta.update(
            {
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "nodata": nodata,
                "compress": compress,
            }
        )

        with rasterio.open(dst_path, "w", **out_meta) as dst:
            dst.write(out_image)

        src_pixels = src.width * src.height * src.count
        dst_pixels = out_image.shape[1] * out_image.shape[2] * out_image.shape[0]

        return {
            "src_shape": (src.count, src.height, src.width),
            "dst_shape": tuple(out_image.shape),
            "pixels_removed": src_pixels - dst_pixels,
            "nodata": nodata,
        }


def clip_info(src_path: str | pathlib.Path) -> dict:
    """Quick summary of a clipped raster for verification."""
    with rasterio.open(src_path) as src:
        return {
            "bands": src.count,
            "width": src.width,
            "height": src.height,
            "crs": str(src.crs),
            "bounds": [src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top],
            "transform": list(src.transform),
            "nodata": src.nodata,
        }
