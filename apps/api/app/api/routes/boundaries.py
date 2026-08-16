"""Boundary endpoints (Phase 2 — Study Area)."""

import json

from fastapi import APIRouter, HTTPException

from app.core import db

router = APIRouter()


@router.get("/boundaries/city")
def get_city_boundary() -> dict:
    """Return the Lagos State boundary as a GeoJSON FeatureCollection."""
    if not db.is_configured():
        raise HTTPException(status_code=503, detail="Database not configured")

    sql = """
        SELECT ST_AsGeoJSON(geom) AS geom_json, attributes
        FROM boundaries.admin_units
        WHERE level = 'state'
        ORDER BY id
        LIMIT 1;
    """
    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                row = cur.fetchone()
    except Exception as exc:  # noqa: BLE001 - surface as 503 for the client
        raise HTTPException(status_code=503, detail=f"Database query failed: {exc}") from exc

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="No state boundary loaded. Run scripts/load_boundaries.py first.",
        )

    feature = {
        "type": "Feature",
        "properties": row["attributes"],
        "geometry": json.loads(row["geom_json"]),
    }
    return {"type": "FeatureCollection", "features": [feature]}
