"""Acquisition configuration (Phase 3 — Landsat pipeline).

Single source of truth for the imagery acquisition parameters documented
in ``docs/04_methodology.md`` (section 3.1) and ``docs/03_datasets.md``.
Keeping every tunable here is what makes the workflow reproducible:
the same inputs always produce the same query and the same selection.

Source: Landsat 8/9 Collection 2 Level-2 via Google Earth Engine.
"""

from __future__ import annotations

import pathlib

# --- Catalog ---
# Collection 2 Level-2 surface reflectance + surface temperature.
COLLECTIONS = [
    "LANDSAT/LC08/C02/T1_L2",
    "LANDSAT/LC09/C02/T1_L2",
]

# WRS-2 path/row covering Lagos State (single scene per date).
WRS_PATH = 191
WRS_ROW = 55

# --- Selection ---
# Default cloud-cover ceiling (percent). Methodology target: <10-20%;
# the median of that range is used as the default and is overridable
# per run (--cloud-threshold). Scenes above the threshold are only used
# as a documented fallback when no scene in the window qualifies.
CLOUD_THRESHOLD_PCT = 15

# Seasonal sampling windows (methodology 3.1). ``(start_month, end_month)``
# inclusive; the dry window crosses the year boundary (Nov-Mar).
SEASONAL_WINDOWS: dict[str, tuple[int, int]] = {
    "dry": (11, 3),   # November - March
    "wet": (4, 10),   # April - October
}

# --- Bands exported per scene ---
# Surface reflectance for NDVI (B4/B5) and NDBI (B5/B6/B7), the C2 L2
# surface-temperature band, and QA_PIXEL for cloud masking (Phase 4).
BANDS = ["SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10", "QA_PIXEL"]

# --- Export ---
# 30 m native resolution; UTM zone 31N (EPSG:32631) per methodology
# (area-accurate analysis grid); Cloud-Optimized GeoTIFF for delivery.
SCALE_METERS = 30
EXPORT_CRS = "EPSG:32631"
EXPORT_FORMAT = "GeoTIFF"
CLOUD_OPTIMIZED = True
DRIVE_FOLDER = "urban_heat_intelligence"

# --- Local paths ---
ROOT = pathlib.Path(__file__).resolve().parents[2]
# Study-area boundary used as the search/export geometry (Phase 2 output).
GEOMETRY_SOURCE = ROOT / "data" / "processed" / "boundaries" / "lagos_state.geojson"
# Metadata records + downloaded imagery live here; gitignored (3.6).
IMAGERY_DIR = ROOT / "data" / "processed" / "imagery"
MANIFEST_FILE = IMAGERY_DIR / "manifest.json"
