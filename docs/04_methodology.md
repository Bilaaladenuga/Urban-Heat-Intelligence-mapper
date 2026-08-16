# Task 0.4 — Methodology

**Status:** Complete (Phase 0 — Research Design)

This document defines the overall research methodology before implementation begins. Each step is implemented and documented in detail in its corresponding phase. **No formulas or accuracy values are invented here** — equations below are standard published definitions (Rouse et al. 1974 for NDVI; Zha et al. 2003 for NDBI; USGS Collection 2 Level-2 science product conventions for LST scaling).

## 1. End-to-end workflow

```text
Acquisition (Phase 3)          Preprocessing (Phase 4)
─────────────────────          ──────────────────────
Landsat 8/9 C2 L2 (GEE)   →    Cloud mask (QA_PIXEL)
Cloud filter (< threshold)     Clip to Lagos State AOI
Date + extent selection        Align to common grid (UTM 31N)
Metadata capture               Nodata handling

Derived products               Spatial analysis (Phase 8)
─────────────────────          ──────────────────────
NDVI (Phase 5)            →    LST vs NDVI
LST (Phase 6)                  LST vs built-up (NDBI)
NDBI built-up (Phase 7)        LST vs land cover (WorldCover)
                               Zonal stats per LGA

Hotspots (Phase 9)             Temporal (Phase 11)        Delivery (Phase 10/12)
─────────────────────          ─────────────────────      ─────────────────────
High LST + low NDVI       →    ΔLST / ΔNDVI / ΔNDBI   →   Web GIS layers + legends
+ high NDBI categories         between dates               + analytical indicator
```

## 2. Reference systems

| Purpose | CRS |
|---------|-----|
| Raster analysis (area-accurate statistics) | UTM zone 31N (EPSG:32631) — Lagos spans lon 2.7–4.4°E |
| Web delivery / boundary storage | WGS 84 (EPSG:4326) |
| Projection step | Documented in preprocessing (Phase 4.3 raster alignment) |

## 3. Processing steps and equations

### 3.1 Acquisition (Phase 3)
- Source: Landsat 8/9 Collection 2 Level-2 via Google Earth Engine (`LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2`), scene 191/055.
- Selection criteria: cloud cover below a defined threshold (target <10–20%, confirmed per scene), one dry-season and one wet-season date.
- Outputs: surface reflectance + ST bands, QA_PIXEL, and a metadata record (date, sensor, cloud %, scene ID) — **no raw imagery committed to Git**.

### 3.2 Preprocessing (Phase 4)
1. **Cloud masking** using the QA_PIXEL bit flags (cloud, cloud shadow, cirrus) → valid-data mask.
2. **Clipping** to the Lagos State AOI.
3. **Raster alignment**: reproject/resample all bands to a common grid in UTM 31N, matching resolution (30 m) and extent.
4. **Nodata handling**: explicit nodata values; masked/invalid pixels excluded from statistics (never replaced with arbitrary values).

### 3.3 NDVI (Phase 5)

```text
NDVI = (NIR − RED) / (NIR + RED)
```

- Bands: Landsat 8/9 → RED = B4, NIR = B5.
- Output: 30 m NDVI raster, descriptive statistics, visualization, validation against expected range [−1, 1] and known land-cover values (water ≈ negative, vegetation > 0.3+).

### 3.4 Land Surface Temperature (Phase 6)
- Basis: **Landsat Collection 2 Level-2 Surface Temperature band (ST_B10)** — atmospheric correction and emissivity are already applied by USGS in this product, providing a defensible LST basis without inventing coefficients.
- Scaling to physical units (USGS C2 L2 conventions, to be verified in implementation):

```text
LST_K   = ST_B10 × 0.00341802 + 149.0     (Kelvin)
LST_°C  = LST_K − 273.15
```

- Documented in Phase 6: band, scaling, emissivity assumptions (as applied in the C2 L2 product), conversions, and limitations. Exact GEE band handling confirmed against known reference values during implementation.

### 3.5 Built-up analysis (Phase 7)
- Primary indicator: **NDBI** (Zha et al. 2003):

```text
NDBI = (SWIR1 − NIR) / (SWIR1 + NIR)
```

- Bands: SWIR1 = B6, NIR = B5. Positive NDBI values indicate built-up/bare surfaces.
- **Justification:** NDBI highlights urban surfaces using SWIR reflectance where built-up areas are bright. **Known limitation acknowledged:** it also responds to bare soil — mitigated by cross-checking against ESA WorldCover built-up class and GHSL (optional) in the analysis phase.
- Output: 30 m NDBI raster + built-up map.

### 3.6 Spatial analysis (Phase 8)
- **Water masking** applied first (WorldCover water class) so water pixels do not distort vegetation/built-up statistics.
- **Zonal statistics** per LGA (20 units): mean, median, percentiles, spread of LST/NDVI/NDBI.
- **Pairwise association:** Pearson and Spearman correlation for LST–NDVI and LST–NDBI, with scatter plots.
- **Regression:** simple linear regression (LST ~ NDVI; LST ~ NDBI); multiple regression (LST ~ NDVI + NDBI) reporting coefficients, R², p-values.
- **Spatial statistics (reported as appropriate):** global Moran's I for LST autocorrelation; Getis-Ord Gi* for hot/cold spot identification (implemented in Phase 9). Spatial autocorrelation caveats documented.

### 3.7 Heat hotspots (Phase 9)
- Threshold-based classification using within-scene quantiles (thresholds finalized with the data):
  - **High heat:** LST above an upper quantile (e.g., 75th/90th).
  - **Low vegetation:** NDVI below a lower quantile.
  - **High built-up:** NDBI above an upper quantile.
- **Categories** (analytical only, not health-risk zones):
  1. All three conditions → *priority* (feeds Phase 12 indicator)
  2. Two conditions → secondary classes
  3. None/one → non-priority
- Labeling rules per spec: never described as health-risk zones without health data.

### 3.8 Temporal analysis (Phase 11)
- Align ≥2 dates (dry + wet season) on the common grid; compute ΔLST, ΔNDVI, ΔNDBI maps and per-LGA change statistics.

### 3.9 Planning insights (Phase 12)
- Decision-support indicator where **high heat + low vegetation + high built-up intensity** coincide (the "priority" hotspot class), clearly labeled as an **analytical indicator** for further investigation.

## 4. Validation strategy (Phase 13)

| Component | Method |
|-----------|--------|
| NDVI | Value-range checks; comparison with known land-cover expectations |
| LST | Physical plausibility (e.g., water bodies near expected surface temperatures); optional context from NOAA ISD weather-station air temperature (not a direct validation — LST ≠ air temperature) |
| Spatial alignment | Visual + numeric checks of raster extents/geotransforms after reprojection |
| Statistics | Cross-check correlations with and without spatial-autocorrelation awareness; report uncertainty |

## 5. Delivery architecture

- Processed rasters exported as cloud-optimized GeoTIFFs; served to the MapLibre frontend as tiled/COG layers with legends and opacity controls (Phase 10).
- Heavy raster processing runs **off the API request path** (precomputed artifacts + scheduled jobs), so the FastAPI backend only serves lightweight, pre-built results (Phase 15).
- All processing code lives in `remote_sensing/` and `analysis/` with tests in `tests/` (Phase 14).
