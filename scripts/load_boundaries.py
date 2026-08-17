"""Load study-area boundaries from data/processed/ into PostGIS.

Usage:
    python scripts/load_boundaries.py
    python scripts/load_boundaries.py data/processed/boundaries/lagos_state.geojson

Loads each feature of the given GeoJSON as an admin unit (default level
"state"; override with --level lga). Requires SUPABASE_DB_URL in
apps/api/.env.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core import db  # noqa: E402
from app.services.boundaries import upsert_admin_unit  # noqa: E402

DEFAULT_FILE = ROOT / "data" / "processed" / "boundaries" / "lagos_state.geojson"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geojson", nargs="?", default=str(DEFAULT_FILE))
    parser.add_argument("--level", default="state", choices=["state", "lga", "neighborhood"])
    parser.add_argument("--source", default="ocha_hdx_codab_v01")
    args = parser.parse_args()

    if not db.is_configured():
        print("SUPABASE_DB_URL is not configured (check apps/api/.env). Aborting.")
        return 1

    path = pathlib.Path(args.geojson)
    if not path.exists():
        print(f"ERROR: {path} does not exist. Run scripts/fetch_lagos_boundary.py first.")
        return 1

    with path.open(encoding="utf-8") as f:
        fc = json.load(f)

    features = fc.get("features", [])
    if not features:
        print("ERROR: GeoJSON contains no features.")
        return 1

    print(f"==> Loading {len(features)} feature(s) from {path} (level={args.level})")
    inserted = 0
    # One connection for the whole batch — opening a connection per
    # feature is slow over the Supabase pooler (Task 2.3 lesson).
    with db.connect() as conn:
        for feature in features:
            if upsert_admin_unit(feature, level=args.level, source=args.source, conn=conn):
                inserted += 1
        conn.commit()
    print(f"==> Done: {inserted} upserted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
