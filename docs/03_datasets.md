# Task 0.3 — Datasets

**Status:** Complete (Phase 0 — Research Design)

Data rules: raw downloads → `data/raw/` (gitignored); processed rasters → `data/processed/` (gitignored). Imagery is never committed to Git (Phase 3.6). Google Earth Engine exports are reproducible via the acquisition pipeline with deterministic asset IDs.

## Core datasets

### 1. Landsat 8/9 Collection 2 Level-2 (primary)

| Attribute | Value |
|-----------|-------|
| Source | NASA/USGS via Google Earth Engine (`LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2`) |
| Scene | WRS-2 path 191, row 055 |
| Resolution | 30 m (surface reflectance; ST band delivered at 30 m, resampled from 100 m native TIRS) |
| Format | Cloud-optimized GeoTIFF (GEE export) |
| License | USGS public domain |

**Bands used and purpose:**

| Band | Use |
|------|-----|
| Red (B4), NIR (B5) | NDVI |
| NIR (B5), SWIR1 (B6), SWIR2 (B7) | NDBI (built-up indicator) |
| ST_B10 (Surface Temperature) | LST — Collection 2 Level-2 already applies atmospheric correction and emissivity; provides a defensible LST basis |
| QA_PIXEL | Cloud/cloud-shadow/snow masking |

**Acquisition plan (tentative):** ≥2 scenes — one dry-season (~Nov–Mar), one wet-season (~Apr–Oct) — low cloud cover (<10–20%, confirmed via scene metadata). Exact dates selected in Phase 3 with the acquisition pipeline.

### 2. Administrative boundaries

| Dataset | Source | Detail | Use |
|---------|--------|--------|-----|
| Lagos State boundary + LGAs | GADM (gadm.org) or OCHA/HDX Nigeria Admin 2 | GeoPackage/GeoJSON, EPSG:4326 | AOI, zonal statistics units |
| Neighborhoods / LCDAs | OpenStreetMap (Geofabrik Nigeria extract) | Boundary relations / place polygons | Neighborhood display layer (Phase 2) |

License: GADM free for non-commercial use; OSM ODbL (attribution required). **Source chosen in Phase 2: OCHA HDX COD-AB** (CC BY-IGO) — `nga_admin_boundaries.geojson.zip` provides admin-0..3 (37 states, 774 LGAs) in one file; fetched via `scripts/fetch_lagos_boundary.py`.

### 3. Land cover

| Dataset | Source | Resolution | Year | Use |
|---------|--------|-----------|------|-----|
| ESA WorldCover | ESA (worldcover.esa.int) | 10 m, 11 classes | v200 (2020/2021) | Land-cover layer (Phase 10); cross-check for built-up mapping |

License: CC BY 4.0 (attribution required).

### 4. Built-up density (supplementary)

| Dataset | Source | Use |
|---------|--------|-----|
| GHSL Built-up Surface (GHSL BUILT-S) | European Commission JRC | Optional cross-check against the NDBI-derived built-up map (Phase 7) |

Primary built-up indicator is **NDBI from Landsat** per Phase 7; GHSL used only for validation/comparison, not as the main layer.

### 5. Elevation (optional context)

| Dataset | Source | Resolution | Use |
|---------|--------|-----------|-----|
| SRTM | NASA/USGS via GEE | ~30 m (1 arc-sec) | Optional context; Lagos is flat so low priority — may be skipped |

### 6. Validation data (optional, hedged)

| Dataset | Source | Use |
|---------|--------|-----|
| Weather-station air temperature | NOAA ISD / NCEI stations around Lagos | Sanity check of LST against air temperature (not a direct validation — LST ≠ air temperature); only if stations with usable records are found |

## Data-role summary

| Research need | Dataset |
|---------------|---------|
| Vegetation (NDVI) | Landsat 8/9 C2 L2 |
| Land surface temperature | Landsat 8/9 C2 L2 ST_B10 |
| Built-up intensity | Landsat NDBI (+ GHSL cross-check) |
| Land cover | ESA WorldCover |
| Boundaries (state/LGA/neighborhood) | GADM / OCHA HDX + OSM |
| Temporal comparison | Landsat scenes from ≥2 dates (dry + wet season) |

## Open items (resolved in later phases)

- Exact Landsat acquisition dates (Phase 3, via cloud-filtered search).
- Boundary source decision (Phase 2).
- Whether SRTM and GHSL are needed (Phase 7/8 decision).
