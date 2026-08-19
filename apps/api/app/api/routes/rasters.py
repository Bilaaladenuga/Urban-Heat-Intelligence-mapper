"""Raster endpoints — tile serving and metadata for preprocessed scenes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.services.rasters import list_scenes, render_tile

router = APIRouter(prefix="/rasters")


@router.get("", summary="List available preprocessed scenes")
def get_scenes() -> dict:
    """Return metadata for all preprocessed scenes."""
    scenes = list_scenes()
    return {"scenes": scenes, "count": len(scenes)}


@router.get("/{scene_id}/info", summary="Scene metadata")
def get_scene_info(scene_id: str) -> dict:
    """Return detailed metadata for a specific scene."""
    scenes = list_scenes()
    for s in scenes:
        if s["scene_id"] == scene_id:
            return s
    raise HTTPException(status_code=404, detail=f"Scene not found: {scene_id}")


@router.get(
    "/{scene_id}/tiles/{z}/{x}/{y}.png",
    summary="Render an XYZ tile as PNG",
    responses={200: {"content": {"image/png": {}}}},
)
def get_tile(
    scene_id: str,
    z: int,
    x: int,
    y: int,
    band: int = Query(1, ge=1, le=6, description="Band number (1-6)"),
    colormap: str | None = Query(
        None, description="Color map: 'thermal', 'ndvi', or None for grayscale"
    ),
) -> Response:
    """Render a single web-mercator tile for the given scene.

    Band mapping for preprocessed scenes:
    - 1: SR_B4 (Red)
    - 2: SR_B5 (NIR)
    - 3: SR_B6 (SWIR1)
    - 4: SR_B7 (SWIR2)
    - 5: ST_B10 (Surface Temperature)
    - 6: QA_PIXEL

    Colormaps:
    - thermal: blue → cyan → yellow → red (for LST)
    - ndvi: brown → yellow → green (for vegetation)
    - None: grayscale
    """
    png_bytes = render_tile(scene_id, z, x, y, band=band, colormap=colormap)
    if png_bytes is None:
        raise HTTPException(status_code=404, detail="Tile not found")
    return Response(content=png_bytes, media_type="image/png")
