"""Fetch Lagos neighborhoods from OpenStreetMap and save them as GeoJSON.

Source: OpenStreetMap via the Overpass API (ODbL, attribution required).
    Query: place = suburb | neighbourhood | quarter within the Lagos State
    bounding box. Nodes become Point features, closed ways become Polygon
    features (see ``osm_elements_to_features`` in the API service layer).

The result is clipped to the Lagos State boundary (``lagos_state.geojson``,
produced by ``fetch_lagos_boundary.py``) so only places inside the study
area are kept.

Usage:
    python scripts/fetch_lagos_neighborhoods.py
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.services.boundaries import osm_elements_to_features  # noqa: E402

# Lagos State bounding box, from the loaded boundary (EPSG:4326):
#   lon 2.7022-4.3508 E, lat 6.3708-6.6984 N  (south, west, north, east)
BBOX = (6.3708, 2.7022, 6.6984, 4.3508)

# Public Overpass instances, tried in order (the primary one is frequently
# overloaded; the others are mirrors).
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
]

QUERY_TEMPLATE = """\
[out:json][timeout:120];
(
  node["place"~"^(suburb|neighbourhood|quarter)$"]({s},{w},{n},{e});
  way["place"~"^(suburb|neighbourhood|quarter)$"]({s},{w},{n},{e});
);
out body geom;
"""

OUT_PROCESSED_DIR = ROOT / "data" / "processed" / "boundaries"
OUT_GEOJSON = OUT_PROCESSED_DIR / "lagos_neighborhoods.geojson"
STATE_GEOJSON = OUT_PROCESSED_DIR / "lagos_state.geojson"


def fetch_elements() -> list[dict]:
    """Query Overpass (with retries across mirrors) and return elements."""
    query = QUERY_TEMPLATE.format(s=BBOX[0], w=BBOX[1], n=BBOX[2], e=BBOX[3]).encode()
    last_error: Exception | None = None
    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(3):
            try:
                request = urllib.request.Request(
                    endpoint,
                    data=query,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                with urllib.request.urlopen(request, timeout=180) as resp:
                    data = json.load(resp)
                if "elements" in data:
                    print(f"    {endpoint} (attempt {attempt + 1}): "
                          f"{len(data['elements'])} elements")
                    return data["elements"]
                last_error = RuntimeError(f"{endpoint}: no 'elements' in response")
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                print(f"    {endpoint} attempt {attempt + 1} failed: {exc}")
                time.sleep(3)
    raise SystemExit(f"ERROR: all Overpass endpoints failed. Last error: {last_error}")


def clip_to_state(features: list[dict]) -> list[dict]:
    """Keep only features intersecting the Lagos State boundary polygon."""
    from shapely.geometry import shape

    with STATE_GEOJSON.open(encoding="utf-8") as f:
        state = json.load(f)
    polygon = shape(state["features"][0]["geometry"])
    kept = [f for f in features if polygon.intersects(shape(f["geometry"]))]
    print(f"    clipped {len(features)} -> {len(kept)} inside the state boundary")
    return kept


def main() -> int:
    OUT_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("==> Querying OpenStreetMap (Overpass) for Lagos neighborhoods")
    elements = fetch_elements()

    print("==> Converting elements to GeoJSON features")
    features = osm_elements_to_features(elements)
    print(f"    {len(features)} named places (points + polygons)")

    print("==> Clipping to the Lagos State boundary")
    features = clip_to_state(features)
    if not features:
        print("ERROR: no features remain after clipping — aborting.")
        return 1

    polygons = sum(1 for f in features if f["geometry"]["type"] == "Polygon")
    OUT_GEOJSON.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"==> Wrote {OUT_GEOJSON}")
    print(f"    {len(features)} features ({polygons} polygons, "
          f"{len(features) - polygons} points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
