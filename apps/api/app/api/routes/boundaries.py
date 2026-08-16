"""Boundary endpoints (Phase 2 — Study Area)."""

import json

from fastapi import APIRouter, HTTPException

from app.core import db

router = APIRouter()


def _query_admin_units(level: str) -> list[dict]:
    """Return all features for an admin level as GeoJSON feature dicts."""
    if not db.is_configured():
        raise HTTPException(status_code=503, detail="Database not configured")

    sql = """
        SELECT name, pcode, ST_AsGeoJSON(geom) AS geom_json, attributes
        FROM boundaries.admin_units
        WHERE level = %s
        ORDER BY name;
    """
    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (level,))
                rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001 - surface as 503 for the client
        raise HTTPException(status_code=503, detail=f"Database query failed: {exc}") from exc

    features = [
        {
            "type": "Feature",
            "properties": {"name": row["name"], "pcode": row["pcode"], **row["attributes"]},
            "geometry": json.loads(row["geom_json"]),
        }
        for row in rows
    ]
    return features


@router.get("/boundaries/city")
def get_city_boundary() -> dict:
    """Return the Lagos State boundary as a GeoJSON FeatureCollection."""
    features = _query_admin_units("state")
    if not features:
        raise HTTPException(
            status_code=404,
            detail="No state boundary loaded. Run scripts/load_boundaries.py first.",
        )
    return {"type": "FeatureCollection", "features": features}


@router.get("/boundaries/lgas")
def get_lgas() -> dict:
    """Return all Lagos LGAs as a GeoJSON FeatureCollection."""
    features = _query_admin_units("lga")
    if not features:
        raise HTTPException(
            status_code=404,
            detail="No LGA boundaries loaded. Run scripts/load_boundaries.py --level lga first.",
        )
    return {"type": "FeatureCollection", "features": features}
