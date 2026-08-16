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
- **Sampling design (tentative, finalized in Phase 3):**
  - **Seasonal windows:** dry season Nov–Mar, wet season Apr–Oct (with the August dry-break noted). One acquisition per window, cloud-filtered.
  - **Scene pairing:** dates chosen to be as close as possible to the same time of year where the temporal comparison is seasonal; otherwise one dry + one wet for seasonality contrast. Pairing rationale recorded in the acquisition metadata.
  - **Cloud fallback:** if no scene meets the cloud threshold in a window, the next closest low-cloud date is taken and the deviation recorded — never force a cloudy scene.
- Outputs: surface reflectance + ST bands, QA_PIXEL, and a metadata record (date, sensor, cloud %, scene ID, selection rationale) — **no raw imagery committed to Git**.

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
- Output: 30 m NDVI raster, descriptive statistics, visualization, and validation against expected range [−1, 1].
- **Value validation (Phase 5.4):**
  - Range check: all valid pixels within [−1, 1]; values outside → investigate (masking/processing error).
  - Known land-cover expectations: water ≈ negative values, dense vegetation ≈ 0.4–0.9, bare/urban ≈ ≤ 0.2 (rough reference bands, not thresholds).
  - Spatial check: NDVI pattern vs a true-color composite and vs WorldCover (vegetation classes where NDVI is high).

### 3.4 Land Surface Temperature (Phase 6)

**Chosen basis: Landsat Collection 2 Level-2 Surface Temperature (ST_B10).** USGS generates this band by applying atmospheric correction and surface-emissivity adjustment (using the ASTER Global Emissivity Dataset) through a single-channel algorithm, then publishing it as a standard product. Using it means we do **not** derive emissivity or atmospheric corrections ourselves — the defensible, documented choice given the project rule *"do not invent formulas or accuracy values"*.

- **Scaling to physical units** (USGS C2 L2 conventions; exact GEE band handling verified in Phase 6 implementation):

```text
LST_K   = ST_B10 × 0.00341802 + 149.0     (Kelvin)
LST_°C  = LST_K − 273.15
```

- **What we deliberately do NOT do:** reconstruct LST from Collection 1 or Level-1 thermal radiance (i.e., TOA radiance Lλ = M_L·Q_cal + A_L, brightness temperature BT = K₂/ln(K₁/Lλ + 1), then a user-supplied emissivity). That path requires per-scene thermal constants and an emissivity assumption we would have to invent; the C2 L2 product removes that burden.
- **Emissivity assumption note:** the product's emissivity input is a global dataset; residual emissivity uncertainty remains and is documented in Phase 6 and Phase 13. **No accuracy numbers are claimed.**
- **Verification in Phase 6:** after scaling, check physical plausibility against known references — e.g., open water bodies and the lagoon should fall in a narrow, expected surface-temperature range; urban pixels should generally exceed vegetated pixels. The scaling formula above is confirmed in code against the GEE-delivered band values before any analysis proceeds.
- **Phase 6 deliverables:** documented bands, scaling, emissivity assumptions, conversions, and limitations (`remote_sensing/lst/` + docs).

### 3.5 Built-up analysis (Phase 7)
- Primary indicator: **NDBI** (Zha et al. 2003):

```text
NDBI = (SWIR1 − NIR) / (SWIR1 + NIR)
```

- Bands: SWIR1 = B6, NIR = B5. Positive NDBI values indicate built-up/bare surfaces.
- **Justification:** NDBI highlights urban surfaces using SWIR reflectance where built-up areas are bright. **Known limitation acknowledged:** it also responds to bare soil — mitigated by cross-checking against ESA WorldCover built-up class and GHSL (optional) in the analysis phase.
- Output: 30 m NDBI raster + built-up map.

### 3.6 Spatial analysis (Phase 8)

**Water masking (applied before all pixel-level statistics):** derive a water mask from the ESA WorldCover water class, resampled to the 30 m analysis grid, and exclude water pixels from vegetation/built-up/LST statistics so the lagoon and creeks do not distort results. Mask choice is recorded as a documented decision (Phase 8); NDWI-based masking is the fallback alternative if WorldCover water disagrees with the imagery.

**Analysis units and sampling design (to mitigate spatial autocorrelation and MAUP):**
- **Pixel level:** association statistics over the full valid-pixel population (all non-masked, non-water pixels in the AOI).
- **Unit level:** LGA-level (20 units) zonal statistics — mean, median, percentiles, interquartile spread of LST/NDVI/NDBI per LGA.
- **Autocorrelation awareness:** global Moran's I computed for LST; where practical, a subsample of pixels spaced ≥ ~300 m apart is used for a check that is less inflated by spatial dependence. All p-values are reported with the caveat that pixel-level tests are not fully independent.

**Statistical tests (defaults: two-sided, α = 0.05, reported with caveats):**
- **Pairwise association:** Pearson and Spearman correlation for LST–NDVI and LST–NDBI, with scatter plots (pixel-level and LGA-mean level).
- **Regression:** simple linear regression (LST ~ NDVI; LST ~ NDBI) and multiple regression (LST ~ NDVI + NDBI) reporting coefficients, R², p-values; residual maps checked for spatial structure.
- **Spatial statistics (reported as appropriate):** global Moran's I for LST autocorrelation; Getis-Ord Gi* for hot/cold spot identification (implemented in Phase 9).

### 3.7 Heat hotspots (Phase 9)

**Threshold definition (data-driven, transparent, reproducible):** within-scene quantiles computed over the valid, water-masked pixel population. Default quantiles (finalized in Phase 9 with justification):

| Condition | Rule (default) |
|-----------|----------------|
| High heat | LST > 75th percentile of valid pixels |
| Low vegetation | NDVI < 25th percentile of valid pixels |
| High built-up | NDBI > 75th percentile of valid pixels |

**Hotspot categories** (analytical only — **never** described as health-risk zones without health data):

| Category | Condition combination | Label |
|----------|----------------------|-------|
| 3 of 3 | High heat + low veg + high built-up | **Priority** (feeds Phase 12 indicator) |
| 2 of 3 | Any two conditions | Secondary — heat–veg / heat–builtup / veg–builtup |
| 1 of 3 | Any single condition | Elevated |
| 0 of 3 | No condition met | Baseline |

- Category definitions and the chosen quantiles are recorded with the outputs (Phase 9).
- Getis-Ord Gi* (from Phase 8) is used as a spatial check on whether Priority pixels cluster.
- Labeling rules per spec: analytical indicator language only; no health claims.

### 3.8 Temporal analysis (Phase 11)
- Align ≥2 dates (dry + wet season) on the common grid; compute ΔLST, ΔNDVI, ΔNDBI maps and per-LGA change statistics.
- **Valid-pixel consistency:** change maps only include pixels valid (non-masked, non-water) on **both** dates, so differences are not artifacts of different masks.
- **Outputs:** per-pixel Δ maps (°C change in LST; ΔNDVI; ΔNDBI) and per-LGA summary statistics of change. Results are reported as date-pair differences, **not** rates or trends (per limitations).

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

## 6. Quality control checklist (applied per scene and per product)

| Check | Where | Pass criteria |
|-------|-------|---------------|
| Cloud cover | Acquisition (Phase 3) | Below threshold (target <10–20%); deviation recorded |
| Valid-pixel fraction | Preprocessing (Phase 4) | QA_PIXEL mask leaves a usable land fraction in the AOI |
| Grid consistency | Preprocessing (Phase 4) | All bands: same CRS (UTM 31N), 30 m resolution, matching extent/geotransform |
| NDVI range | Phase 5 | All valid pixels within [−1, 1] |
| LST range | Phase 6 | No physically implausible values (outside ~250–340 K); water/urban ordering sanity check |
| Alignment | Phase 4/13 | Visual + geotransform comparison across layers |
| Metadata | All phases | Scene ID, date, sensor, cloud %, processing parameters recorded with every artifact |
| Tests | Phase 14 | Every processing function covered by automated tests in `tests/` |
