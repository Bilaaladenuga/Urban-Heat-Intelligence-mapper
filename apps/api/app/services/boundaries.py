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


def osm_elements_to_features(elements: list[dict]) -> list[dict]:
    """Convert Overpass API elements into GeoJSON neighborhood features.

    - Nodes become Point features; closed ways become Polygon features.
    - Elements without a ``name`` or ``place`` tag are skipped, as are
      unclosed ways (no usable polygon).
    - When the same name exists as both a point and a polygon, the
      polygon wins (a real boundary is more useful than a label point).

    Source: OpenStreetMap via the Overpass API (ODbL, attribution
    required — recorded in the feature properties).
    """
    features: dict[str, dict] = {}  # name -> feature (polygon preferred)
    order: list[str] = []
    for element in elements:
        tags = element.get("tags", {}) or {}
        name = (tags.get("name") or "").strip()
        if not name or not tags.get("place"):
            continue

        if element["type"] == "node":
            lon, lat = element.get("lon"), element.get("lat")
            if lon is None or lat is None:
                continue
            geometry = {"type": "Point", "coordinates": [lon, lat]}
            rank = 0
        elif element["type"] == "way":
            points = [(p["lon"], p["lat"]) for p in element.get("geometry", [])]
            if len(points) < 4 or points[0] != points[-1]:
                continue  # not a closed ring — no usable polygon
            geometry = {"type": "Polygon", "coordinates": [points]}
            rank = 1
        else:
            continue  # relations not handled for this layer

        if name in features and rank <= features[name]["_rank"]:
            continue
        if name not in features:
            order.append(name)
        features[name] = {
            "type": "Feature",
            "properties": {
                "name": name,
                "place": tags.get("place"),
                "osm_type": element["type"],
                "osm_id": element.get("id"),
            },
            "geometry": geometry,
            "_rank": rank,
        }

    result = []
    for name in order:
        feature = features[name]
        feature.pop("_rank")
        result.append(feature)
    return result


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
    conn=None,
) -> bool:
    """Upsert a single GeoJSON feature into ``boundaries.admin_units``.

    Returns True when a row was inserted or updated. Requires a configured
    database connection (``SUPABASE_DB_URL``). Pass a shared ``conn`` to
    batch several upserts in one connection (the loader does this to
    avoid reconnecting per feature); otherwise a connection is opened and
    closed per call.
    """
    props = feature.get("properties", {})
    geometry = feature.get("geometry")
    if geometry is None:
        raise ValueError("feature has no geometry")

    name_key, pcode_key = _LEVEL_PROPS[level]
    # ``name`` is the generic property used by OSM-sourced features;
    # the HDX COD-AB features only carry adm*_name, so this fallback is
    # a no-op for the state/LGA layers.
    name = (
        props.get(name_key)
        or props.get("adm1_name")
        or props.get("adm0_name")
        or props.get("name")
    )
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
    def _execute(c):
        with c.cursor() as cur:
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
            return cur.fetchone()

    if conn is not None:
        # Caller owns the connection/transaction — no commit here.
        row = _execute(conn)
    else:
        with db.connect() as conn:
            row = _execute(conn)
            conn.commit()
    logger.info("upserted %s boundary %r (id=%s)", level, name, row["id"] if row else None)
    return row is not None
