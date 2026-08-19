# Task 4.x — Preprocessing

**Status:** Complete (Phase 4 — Preprocessing)

This document records the preprocessing steps applied to Landsat Collection 2 Level-2 imagery before analysis. Every decision below is traceable to `docs/04_methodology.md` (section 3.2).

## 1. Overview

```
Raw imagery (Phase 3)         Preprocessed output
────────────────────────      ─────────────────────────
data/raw/imagery/            data/processed/imagery/
  {scene_id}/                  {scene_id}/
    {scene_id}.tif               {scene_id}_processed.tif
    (6 bands, UTM 31N)          (6 bands, UTM 31N, clipped)
```

**Input:** 6-band GeoTIFFs (SR_B4, SR_B5, SR_B6, SR_B7, ST_B10, QA_PIXEL), EPSG:32631, 30 m, uint16.

**Output:** Same structure with cloud-masked, clipped, nodata-validated bands.

## 2. Cloud masking

**Module:** `remote_sensing/preprocessing/cloud_mask.py`

**Source:** Landsat Collection 2 Level-2 QA_PIXEL band (USGS documentation).

### QA_PIXEL bit layout

| Bit | Name | Effect on mask |
|-----|------|----------------|
| 0 | Fill | Mask (no-data) |
| 1 | Dilated Cloud | Mask |
| 2 | Cirrus | Mask |
| 3 | Cloud | Mask |
| 4 | Cloud Shadow | Mask |
| 5 | Snow | Mask (opt-in, excluded by default for Lagos) |
| 6 | Clear | **Inverted** — set = pixel IS clear, do NOT mask |
| 7 | Water | Not masked (handled in Phase 8 via WorldCover) |
| 8–9 | Cloud Shadow Confidence | Not used for masking |
| 10–11 | Cloud Confidence | Not used for masking |
| 12–13 | Snow Confidence | Not used for masking |
| 14–15 | Cirrus Confidence | Not used for masking |

**Important:** Bit 6 (Clear) is **inverted** — when set, the pixel is clear. It is NOT a cirrus flag. The original implementation incorrectly used bit 6 as Cirrus, which masked out 99% of valid pixels. This was fixed by verifying the actual bit layout against real scene data.

### Results

| Scene | Valid pixels | Masked | Notes |
|-------|-------------|--------|-------|
| LC09_191055_20221219 (dry) | 81.4% | 18.6% | Mostly fill from ocean/lagoon at scene edges |
| LC08_191055_20231027 (wet) | 41.4% | 58.6% | High cloud cover (35.4% scene cloud, plus shadows) |

### Validation

- Range check: all valid SR pixels within [0, 65535] (uint16).
- ST_B10 raw values: [44732, 56451] for LC09 — physically plausible after scaling.
- No pixels exceed uint16 range.

## 3. Clipping

**Module:** `remote_sensing/preprocessing/clip.py`

**Method:** `rasterio.mask.mask()` with the Lagos State boundary polygon (Phase 2 output: `data/processed/boundaries/lagos_state.geojson`, reprojected to UTM 31N).

The boundary polygon is a subset of the raster's bounding box — the GEE export already used the boundary bbox, so the raster dimensions stay the same. Clipping masks the ocean, lagoon, and areas outside the state polygon (water, neighbouring states).

**Result:** 33.3% of pixels in the LC09 scene are set to nodata by clipping (ocean, lagoon, areas outside the polygon boundary).

## 4. Alignment

**Module:** `remote_sensing/preprocessing/align.py`

**Reference grid:** EPSG:32631, 30 m resolution (per methodology §2).

Both scenes were exported from GEE with identical parameters, so they share the same CRS, resolution, and bounding box. The alignment step verifies this constraint:

- Both scenes: CRS=EPSG:32631 ✓, resolution=30m ✓, bounds=[467040, 704370, 649410, 740430] ✓
- Output grids are identical — pixel-by-pixel operations (NDVI, NDBI, change detection) are valid.

If a future scene fails the alignment check, the `resample_to_grid()` function reprojects/resamples it to the reference grid.

## 5. Nodata handling

**Module:** `remote_sensing/preprocessing/nodata.py`

**Convention:** nodata = 0 for all bands.

- Masked/invalid pixels are set to 0 (never filled with arbitrary values like mean or interpolation).
- Downstream code excludes nodata=0 pixels from all statistics.
- Water pixels are NOT masked here — handled separately in Phase 8 using ESA WorldCover.

### Validation per band

| Band | Min (valid) | Max (valid) | Nodata % | Status |
|------|------------|------------|----------|--------|
| SR_B4 (Red) | 7764 | 35475 | 51.9% | ✓ |
| SR_B5 (NIR) | 7724 | 49529 | 51.9% | ✓ |
| SR_B6 (SWIR1) | 7578 | 65270 | 51.9% | ✓ |
| SR_B7 (SWIR2) | 7467 | 65454 | 51.9% | ✓ |
| ST_B10 (Temp) | 44732 | 56451 | 51.9% | ✓ |
| QA_PIXEL | 21824 | 22080 | 51.9% | ✓ |

Nodata % includes both cloud-masked and clipped pixels (fill from ocean/lagoon).

## 6. Pipeline CLI

```bash
# Process all scenes:
python -m remote_sensing.preprocessing.pipeline

# Process a specific scene:
python -m remote_sensing.preprocessing.pipeline --scene LC09_191055_20221219

# Process by year:
python -m remote_sensing.preprocessing.pipeline --year 2023

# Dry run (validate only):
python -m remote_sensing.preprocessing.pipeline --scene LC09_191055_20221219 --dry-run
```

## 7. Testing

42 tests across 4 modules:

- `test_preprocessing_cloud_mask.py` — 14 tests (bit logic, realistic values, edge cases)
- `test_preprocessing_clip.py` — 6 tests (boundary loading, reprojection, clipping, nodata)
- `test_preprocessing_align.py` — 8 tests (CRS, resolution, bounds, reference grid)
- `test_preprocessing_nodata.py` — 10 tests (validation, ranges, summary)

Full suite: 64 tests (22 acquisition + 20 API + 42 preprocessing) — all passing.

## 8. Known limitations

- **Cloud masking uses only QA_PIXEL bits** — does not use the confidence bits (8–15) for a graduated mask. For this project's purposes (urban heat analysis with ≥2 scenes), a binary mask is sufficient.
- **Snow masking is excluded by default** — snow is extremely rare in Lagos (tropical); enabling it would add noise without benefit.
- **Water masking is deferred to Phase 8** — the preprocessing step does not exclude water pixels; they are masked using ESA WorldCover in the analysis phase.
- **SR band values may exceed 10000** — C2 L2 uint16 values can reach ~65000 for bright surfaces; the 0.0000275 scaling factor is applied in Phase 5 (NDVI/NDBI computation), not during preprocessing.
