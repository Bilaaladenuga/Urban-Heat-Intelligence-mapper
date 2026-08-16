"""Boundary data handling (Phase 2 — Study Area).

Pure helpers for extracting administrative units from the HDX COD-AB
Nigeria GeoJSON and upserting them into PostGIS.

Source: OCHA HDX "Nigeria - Subnational Administrative Boundaries"
(COD-AB), https://data.humdata.org/dataset/cod-ab-nga (CC BY-IGO).
"""

from __future__ import annotations

import json
import logging

from app.core import db

logger = logging.getLogger(__name__)


def extract_state(feature_collection: dict, state_name: str) -> dict | None:
    """Return the admin-1 feature for ``state_name`` (e.g. "Lagos")."""
    for feature in feature_collection.get("features", []):
        props = feature.get("properties", {})
        # admin-1 rows carry adm1_name; admin-2 rows also carry adm1_name
        # (the parent), so require that adm2_name is absent.
        if props.get("adm1_name") == state_name and not props.get("adm2_name"):
            return feature
    return None


def extract_lgas(feature_collection: dict, state_name: str) -> list[dict]:
    """Return all admin-2 (LGA) features belonging to ``state_name``."""
    return [
        feature
        for feature in feature_collection.get("features", [])
        if feature.get("properties", {}).get("adm1_name") == state_name
        and feature.get("properties", {}).get("adm2_name")
    ]


def feature_to_feature_collection(feature: dict) -> dict:
    """Wrap a single feature in a GeoJSON FeatureCollection."""
    return {"type": "FeatureCollection", "features": [feature]}


# Admin-level columns used for name/pcode per ``admin_units.level``.
_LEVEL_PROPS: dict[str, tuple[str, str]] = {
    "state": ("adm1_name", "adm1_pcode"),
    "lga": ("adm2_name", "adm2_pcode"),
    "neighborhood": ("adm3_name", "adm3_pcode"),
}


def upsert_admin_unit(
    feature: dict,
    *,
    level: str,
    source: str,
) -> bool:
    """Upsert a single GeoJSON feature into ``boundaries.admin_units``.

    Returns True when a row was inserted or updated. Requires a configured
    database connection (``SUPABASE_DB_URL``).
    """
    props = feature.get("properties", {})
    geometry = feature.get("geometry")
    if geometry is None:
        raise ValueError("feature has no geometry")

    name_key, pcode_key = _LEVEL_PROPS[level]
    name = props.get(name_key) or props.get("adm1_name") or props.get("adm0_name")
    if not name:
        raise ValueError(f"feature has no {name_key}")

    sql = """
        INSERT INTO boundaries.admin_units
            (level, name, pcode, area_sqkm, source, attributes, geom)
        VALUES
            (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
        ON CONFLICT (level, name) DO UPDATE SET
            pcode     = EXCLUDED.pcode,
            area_sqkm = EXCLUDED.area_sqkm,
            source    = EXCLUDED.source,
            attributes = EXCLUDED.attributes,
            geom      = EXCLUDED.geom
        RETURNING id;
    """
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    level,
                    name,
                    props.get(pcode_key),
                    props.get("area_sqkm"),
                    source,
                    json.dumps(props, default=str),
                    json.dumps(geometry),
                ),
            )
            row = cur.fetchone()
        conn.commit()
    logger.info("upserted %s boundary %r (id=%s)", level, name, row["id"] if row else None)
    return row is not None
