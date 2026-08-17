"""Fetch the Lagos State boundary from OCHA HDX and save it as GeoJSON.

Source: "Nigeria - Subnational Administrative Boundaries" (COD-AB)
    https://data.humdata.org/dataset/cod-ab-nga
    License: CC BY-IGO (attribution required)

Downloads the full Nigeria admin-0..3 GeoJSON zip, extracts the admin-1
(State) layer, and writes the Lagos feature to ``data/processed/``.

Usage:
    python scripts/fetch_lagos_boundary.py
"""

from __future__ import annotations

import io
import json
import pathlib
import sys
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.services.boundaries import extract_lgas, extract_state  # noqa: E402

# Resource: nga_admin_boundaries.geojson.zip (GeoJSON)
HDX_URL = (
    "https://data.humdata.org/dataset/cod-ab-nga/resource/"
    "7e30ec96-7f29-4ee8-9f4c-77633b353cbb/download/nga_admin_boundaries.geojson.zip"
)
STATE_NAME = "Lagos"

OUT_RAW_DIR = ROOT / "data" / "raw" / "boundaries"
OUT_PROCESSED_DIR = ROOT / "data" / "processed" / "boundaries"
OUT_RAW_ZIP = OUT_RAW_DIR / "nga_admin_boundaries.geojson.zip"
OUT_GEOJSON = OUT_PROCESSED_DIR / "lagos_state.geojson"
OUT_LGAS_GEOJSON = OUT_PROCESSED_DIR / "lagos_lgas.geojson"


def main() -> int:
    OUT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"==> Downloading {HDX_URL}")
    with urllib.request.urlopen(HDX_URL, timeout=300) as resp:
        data = resp.read()
    OUT_RAW_ZIP.write_bytes(data)
    print(f"    saved {OUT_RAW_ZIP} ({len(data) / 1e6:.1f} MB)")

    print("==> Extracting admin-1 (states) layer")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        with zf.open("nga_admin1.geojson") as f:
            states = json.load(f)

    print(f"    {len(states['features'])} states in file")
    lagos = extract_state(states, STATE_NAME)
    if lagos is None:
        print(f"ERROR: state {STATE_NAME!r} not found in admin-1 layer")
        return 1

    props = lagos["properties"]
    print(f"    found {STATE_NAME}: pcode={props.get('adm1_pcode')}, "
          f"area={props.get('area_sqkm')} km2, "
          f"center=({props.get('center_lon')}, {props.get('center_lat')})")

    # Keep the raw feature as-is; add provenance for the processed file.
    processed = {"type": "FeatureCollection", "features": [lagos]}
    OUT_GEOJSON.write_text(json.dumps(processed), encoding="utf-8")
    print(f"==> Wrote {OUT_GEOJSON}")

    # Quick validation of the geometry.
    geom_type = lagos["geometry"]["type"]
    print(f"    geometry type: {geom_type}")

    # --- LGA layer (Task 2.2) ---
    print("==> Extracting admin-2 (LGA) layer")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        with zf.open("nga_admin2.geojson") as f:
            lgas = json.load(f)

    lagos_lgas = extract_lgas(lgas, STATE_NAME)
    print(f"    {len(lagos_lgas)} LGAs in {STATE_NAME}")
    if not lagos_lgas:
        print(f"ERROR: no LGAs found for {STATE_NAME!r}")
        return 1

    OUT_LGAS_GEOJSON.write_text(
        json.dumps({"type": "FeatureCollection", "features": lagos_lgas}),
        encoding="utf-8",
    )
    print(f"==> Wrote {OUT_LGAS_GEOJSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
