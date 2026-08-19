# Task 5.x — NDVI

**Status:** Complete (Phase 5 — NDVI)

## 1. Equation

```text
NDVI = (NIR − RED) / (NIR + RED)
```

(Rouse et al. 1974, as cited in methodology §3.3)

## 2. Bands

| Role | Landsat 8/9 C2 L2 band | Preprocessed raster band |
|------|------------------------|--------------------------|
| RED | SR_B4 | Band 1 |
| NIR | SR_B5 | Band 2 |

## 3. Scaling

C2 L2 surface reflectance is stored as uint16. USGS scaling:

```text
reflectance = raw_value × 0.0000275 − 0.2
```

The valid reflectance range starts at raw value 7273 (= 0.0 reflectance). Pixels below this threshold are fill or degraded values and are excluded from NDVI computation.

## 4. Results

| Scene | NDVI mean | NDVI range | Valid pixels | Notes |
|-------|-----------|-----------|-------------|-------|
| LC09_191055_20221219 (dry) | 0.4103 | [−0.5506, 0.9095] | 48.1% | Nearly cloud-free; healthy vegetation dominant |
| LC08_191055_20231027 (wet) | 0.4453 | [−0.9994, 0.9995] | 25.4% | Cloudy fallback; high vegetation in wet season |

## 5. Validation

- **Range check:** All valid pixels within [−1, 1] ✓
- **Land-cover expectations:**
  - Water pixels (negative NDVI) present — consistent with lagoon/creeks
  - Dense vegetation (0.4–0.9) dominant — consistent with wet tropical environment
  - Bare/urban (≤ 0.2) present — consistent with Lagos urban core
- **Spatial pattern:** NDVI shows higher values in vegetated areas, lower in urban/water — consistent with expected patterns

## 6. Output

- Rasters: `data/processed/ndvi/{scene_id}/{scene_id}_ndvi.tif` (float32, NaN nodata)
- Manifest: `data/processed/ndvi/ndvi_manifest.json`
- Web display: NDVI layer available in the map via the raster tile endpoint

## 7. Testing

20 tests covering:
- C2 L2 reflectance scaling (5 tests)
- NDVI computation (8 tests: zero, positive, negative, nodata, range, dtype)
- Statistics (3 tests)
- Validation (4 tests)

Full suite: 91/91 passing.
