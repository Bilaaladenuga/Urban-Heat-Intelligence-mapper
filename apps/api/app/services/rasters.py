"""Raster tile service — serves preprocessed GeoTIFFs as XYZ map tiles.

Uses rasterio + mercantile to render individual tiles from the
preprocessed scenes.  Each tile is rendered as a RGBA PNG with a
stretch (percentile clamp) so the data is visible on the map.

Tile scheme: TMS (z/x/y), which is what MapLibre GL expects
when using ``raster-dem`` or ``raster`` sources with ``scheme: 'tms'``.
However, for standard XYZ we use the web-mercator tiling scheme.

References
----------
Methodology §3.9 — Delivery architecture: ``served to the MapLibre
frontend as tiled/COG layers with legends and opacity controls``.
"""

from __future__ import annotations

import pathlib

import mercantile
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject

# --- Paths ---
# rasters.py is at apps/api/app/services/rasters.py
# parents[0] = services, [1] = app, [2] = api, [3] = apps, [4] = repo root
ROOT = pathlib.Path(__file__).resolve().parents[4]
PROCESSED_DIR = ROOT / "data" / "processed" / "imagery"
NDVI_DIR = ROOT / "data" / "processed" / "ndvi"

# Web Mercator CRS for tile rendering.
WEB_MERCATOR = CRS.from_epsg(3857)

# Tile size in pixels.
TILE_SIZE = 256

# Stretch percentiles for visualization (lower/upper).
STRETCH_LOW = 2.0   # 2nd percentile
STRETCH_HIGH = 98.0  # 98th percentile


def list_scenes() -> list[dict]:
    """List all preprocessed scenes + derived products available for tiling."""
    scenes = []
    if not PROCESSED_DIR.exists():
        return scenes
    for scene_dir in sorted(PROCESSED_DIR.iterdir()):
        if not scene_dir.is_dir() or scene_dir.name.startswith("."):
            continue
        tif = scene_dir / f"{scene_dir.name}_processed.tif"
        if tif.exists():
            with rasterio.open(tif) as src:
                scenes.append({
                    "scene_id": scene_dir.name,
                    "bands": src.count,
                    "crs": str(src.crs),
                    "width": src.width,
                    "height": src.height,
                    "bounds": {
                        "west": src.bounds.left,
                        "south": src.bounds.bottom,
                        "east": src.bounds.right,
                        "north": src.bounds.top,
                    },
                    "nodata": src.nodata,
                    "type": "scene",
                })
    # Also list NDVI rasters.
    if NDVI_DIR.exists():
        for scene_dir in sorted(NDVI_DIR.iterdir()):
            if not scene_dir.is_dir() or scene_dir.name.startswith("."):
                continue
            tif = scene_dir / f"{scene_dir.name}_ndvi.tif"
            if tif.exists():
                with rasterio.open(tif) as src:
                    scenes.append({
                        "scene_id": f"{scene_dir.name}_ndvi",
                        "bands": src.count,
                        "crs": str(src.crs),
                        "width": src.width,
                        "height": src.height,
                        "bounds": {
                            "west": src.bounds.left,
                            "south": src.bounds.bottom,
                            "east": src.bounds.right,
                            "north": src.bounds.top,
                        },
                        "nodata": None,
                        "type": "ndvi",
                    })
    return scenes


def get_scene_path(scene_id: str) -> pathlib.Path:
    """Get the path to a scene's GeoTIFF (preprocessed or derived)."""
    # Check preprocessed scenes first.
    path = PROCESSED_DIR / scene_id / f"{scene_id}_processed.tif"
    if path.exists():
        return path
    # Check NDVI rasters (scene_id format: {scene_id}_ndvi).
    if scene_id.endswith("_ndvi"):
        base = scene_id[:-5]  # strip _ndvi
        ndvi_path = NDVI_DIR / base / f"{base}_ndvi.tif"
        if ndvi_path.exists():
            return ndvi_path
    return path  # fallback


def _percentile_stretch(
    band: np.ndarray,
    low: float = STRETCH_LOW,
    high: float = STRETCH_HIGH,
    is_float: bool = False,
) -> tuple[float, float]:
    """Compute percentile-based min/max for stretching."""
    if is_float:
        valid = band[~np.isnan(band)]
    else:
        valid = band[band > 0]  # exclude nodata (0)
    if valid.size == 0:
        return 0.0, 1.0
    vmin = float(np.percentile(valid, low))
    vmax = float(np.percentile(valid, high))
    if vmax <= vmin:
        vmax = vmin + 1.0
    return vmin, vmax


# Cache for global stretch values per scene+band.
_global_stretch_cache: dict[str, tuple[float, float]] = {}


def get_global_stretch(
    scene_id: str,
    band: int = 1,
    low: float = STRETCH_LOW,
    high: float = STRETCH_HIGH,
) -> tuple[float, float]:
    """Compute the global stretch range for a scene by sampling the full raster.

    This is cached so subsequent tile requests use the same vmin/vmax,
    giving consistent visualization across all tiles.
    """
    cache_key = f"{scene_id}:{band}:{low}:{high}"
    if cache_key in _global_stretch_cache:
        return _global_stretch_cache[cache_key]

    tif_path = get_scene_path(scene_id)
    if not tif_path.exists():
        return (0.0, 1.0)

    with rasterio.open(tif_path) as src:
        is_float = np.issubdtype(np.dtype(src.dtypes[band - 1]), np.floating)
        # Read a subsampled version for speed (every 10th pixel).
        data = src.read(
            band,
            out_shape=(max(1, src.height // 10), max(1, src.width // 10)),
            resampling=Resampling.nearest,
        )
        vmin, vmax = _percentile_stretch(data, low, high, is_float=is_float)

    _global_stretch_cache[cache_key] = (vmin, vmax)
    return vmin, vmax


def _band_to_rgba(
    band: np.ndarray,
    vmin: float,
    vmax: float,
    colormap: str | None = None,
    is_float: bool = False,
) -> np.ndarray:
    """Convert a single band to RGBA for PNG rendering.

    Parameters
    ----------
    band : ndarray
        2D array (uint16 or float64).
    vmin, vmax : float
        Stretch range.
    colormap : str, optional
        'thermal' for LST, 'ndvi' for vegetation, None for grayscale.
    is_float : bool
        True if band is float (NaN nodata); False for uint16 (0 nodata).

    Returns
    -------
    rgba : ndarray of uint8, shape (H, W, 4)
    """
    h, w = band.shape

    # Determine valid pixels.
    if is_float:
        valid = ~np.isnan(band)
    else:
        valid = (band > 0) & (band <= vmax * 1.5)

    # Normalize to 0-255.
    normalized = np.zeros_like(band, dtype=np.float64)
    normalized[valid] = np.clip(
        (band[valid].astype(np.float64) - vmin) / (vmax - vmin), 0, 1
    )
    gray = (normalized * 255).astype(np.uint8)

    # Build RGBA.
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    if colormap == "thermal":
        # Blue → Cyan → Yellow → Red
        rgba[:, :, 0] = np.where(valid, np.clip(gray * 2, 0, 255), 0)       # R
        rgba[:, :, 1] = np.where(valid, np.clip(255 - gray * 2, 0, 255), 0)  # G
        rgba[:, :, 2] = np.where(valid, np.clip(255 - gray * 2, 0, 255), 0)  # B
        rgba[:, :, 3] = np.where(valid, 200, 0)                               # A
    elif colormap == "ndvi":
        # Brown → Yellow → Green
        rgba[:, :, 0] = np.where(valid, np.clip(255 - gray * 2, 0, 255), 0)  # R
        rgba[:, :, 1] = np.where(valid, gray, 0)                              # G
        rgba[:, :, 2] = np.where(valid, 50, 0)                                # B
        rgba[:, :, 3] = np.where(valid, 200, 0)                               # A
    else:
        # Grayscale.
        rgba[:, :, 0] = gray
        rgba[:, :, 1] = gray
        rgba[:, :, 2] = gray
        rgba[:, :, 3] = np.where(valid, 200, 0)

    return rgba


def render_tile(
    scene_id: str,
    z: int,
    x: int,
    y: int,
    *,
    band: int = 1,
    colormap: str | None = None,
) -> bytes | None:
    """Render a single XYZ tile as PNG.

    Parameters
    ----------
    scene_id : str
        Scene identifier (folder name under data/processed/imagery/).
    z, x, y : int
        Tile coordinates (web mercator XYZ).
    band : int
        Band number to render (1-indexed).
    colormap : str, optional
        'thermal' for LST, 'ndvi' for vegetation, None for grayscale.

    Returns
    -------
    PNG bytes, or None if the tile is outside the raster extent.
    """
    tif_path = get_scene_path(scene_id)
    if not tif_path.exists():
        return None

    # Compute the tile bounds in web mercator.
    tile_bounds = mercantile.xy_bounds(x, y, z)

    with rasterio.open(tif_path) as src:
        # Check if the tile intersects the raster.
        src_bounds = rasterio.warp.transform_bounds(
            src.crs, WEB_MERCATOR, *src.bounds
        )
        # tile_bounds: (left, bottom, right, top)
        # src_bounds: (left, bottom, right, top)
        if (
            tile_bounds.right < src_bounds[0]
            or tile_bounds.left > src_bounds[2]
            or tile_bounds.top < src_bounds[1]
            or tile_bounds.bottom > src_bounds[3]
        ):
            # Tile is outside raster extent — return transparent PNG.
            return _transparent_png()

        # Read the band into a web-mercator aligned array.
        # Compute the transform for this tile in web mercator.
        dst_transform = from_bounds(
            tile_bounds.left,
            tile_bounds.bottom,
            tile_bounds.right,
            tile_bounds.top,
            TILE_SIZE,
            TILE_SIZE,
        )

        # Reproject the band to web mercator for this tile's extent.
        is_float = np.issubdtype(np.dtype(src.dtypes[band - 1]), np.floating)
        tile_data = np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.float64)
        reproject(
            source=rasterio.band(src, band),
            destination=tile_data,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=WEB_MERCATOR,
            resampling=Resampling.bilinear,
        )

    # Use global stretch (cached) for consistent visualization across all tiles.
    vmin, vmax = get_global_stretch(scene_id, band=band)
    rgba = _band_to_rgba(tile_data, vmin, vmax, colormap=colormap, is_float=is_float)

    # Encode as PNG.
    return _rgba_to_png(rgba)


def _transparent_png() -> bytes:
    """Return a 256x256 transparent PNG."""

    # Minimal valid PNG: 1x1 transparent pixel, scaled up.
    # For simplicity, return an empty PNG.
    # Actually, let's create a proper 256x256 transparent PNG.
    raw = b""
    for _ in range(TILE_SIZE):
        raw += b"\x00" + b"\x00\x00\x00\x00" * TILE_SIZE  # filter byte + RGBA

    return _encode_png(raw, TILE_SIZE, TILE_SIZE, alpha=True)


def _rgba_to_png(rgba: np.ndarray) -> bytes:
    """Encode an RGBA uint8 array as PNG bytes."""
    h, w = rgba.shape[:2]
    # PNG row: filter byte (0) + pixel data.
    raw = b""
    for row in range(h):
        raw += b"\x00"  # filter: None
        raw += rgba[row].tobytes()
    return _encode_png(raw, w, h, alpha=True)


def _encode_png(raw_data: bytes, width: int, height: int, alpha: bool = True) -> bytes:
    """Encode raw pixel data as a minimal PNG."""
    import struct
    import zlib

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    # PNG signature.
    sig = b"\x89PNG\r\n\x1a\n"

    # IHDR.
    color_type = 6 if alpha else 2  # 6 = RGBA, 2 = RGB
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    ihdr = _chunk(b"IHDR", ihdr_data)

    # IDAT.
    compressed = zlib.compress(raw_data, 6)
    idat = _chunk(b"IDAT", compressed)

    # IEND.
    iend = _chunk(b"IEND", b"")

    return sig + ihdr + idat + iend
