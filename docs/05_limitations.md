# Task 0.5 — Limitations (defined before analysis begins)

**Status:** Complete (Phase 0 — Research Design)

Limitations are recorded **before** analysis so they can guide interpretation and be revisited in Phase 13 (validation). Each item notes the impact and, where possible, the mitigation.

## 1. Data limitations

| Limitation | Impact | Mitigation / handling |
|------------|--------|-----------------------|
| 30 m spatial resolution | Sub-pixel features (narrow streets, small green spaces) are mixed into single pixels | Acknowledged; results describe pixel-level (30 m) patterns, not parcels |
| Thermal band native resolution ~100 m (delivered at 30 m) | LST values are resampled from coarser thermal data; fine thermal detail is limited | Use ST_B10 as delivered by USGS C2 L2; no over-interpretation of sub-100 m thermal detail |
| Tropical cloud cover | Fewer usable acquisitions; possible data gaps | Cloud filtering with QA_PIXEL; target <10–20% cloud; dry-season preference |
| Instantaneous overpass (~10:00–10:15 local for Landsat 8/9) | Captures morning surface heating, not the daily maximum or night-time UHI | Results are interpreted as morning overpass LST, not daily extremes |
| Sparse temporal sampling (16-day repeat + clouds) | Only a small number of dates feasible; not a continuous time series | Analysis is date-comparison, explicitly **not** a trend study |
| Landsat data are surface temperature, not air temperature | LST can differ substantially from the air temperatures people experience | Labels and text always say "land surface temperature"; health-related claims excluded |

## 2. Product/algorithm limitations

| Limitation | Impact | Mitigation / handling |
|------------|--------|-----------------------|
| Emissivity handled by the C2 L2 product | Emissivity assumptions are baked into ST_B10 (USGS uses a global emissivity approach); residual uncertainty exists | Use the official product as-is; document assumptions; **no claimed accuracy numbers invented** |
| NDBI also responds to bare soil | Built-up map may overstate built-up on exposed soil | Cross-check with ESA WorldCover built-up class and (optionally) GHSL; report the discrepancy |
| NDVI saturates in dense vegetation / is sensitive to aerosols | Reduced sensitivity in very green or hazy conditions | SR product mitigates atmosphere; acknowledge in Phase 13 |
| Water/coastline mixed pixels | Statistics near coastlines and lagoon edges can be distorted | Water masking with WorldCover water class; document mask choice |
| Administrative boundaries vs actual urban extent | Peri-urban growth may extend beyond LGA boundaries; LGAs are not homogeneous | Report per-LGA results as administrative units, not physical neighborhoods |

## 3. Statistical limitations

| Limitation | Impact | Mitigation / handling |
|------------|--------|-----------------------|
| Correlation ≠ causation | NDVI/NDBI associations with LST do not prove causal effects | Language in results stays correlational |
| Spatial autocorrelation | Nearby pixels are not independent → inflated significance in classical tests | Report Moran's I; use spatial-aware methods where appropriate; caveat p-values |
| MAUP (modifiable areal unit problem) | LGA-level aggregation can change apparent relationships | Also examine neighborhood level where feasible; results are scale-dependent |
| Small number of dates | Any change metrics rest on few observations | Change results reported as date-pair differences, not rates/trends |

## 4. Scope and interpretation limits

- **Single city:** findings apply to Lagos, not Nigeria generally.
- **No health data:** hotspot categories and the Phase 12 indicator are **analytical indicators for further investigation**, never health-risk zones (per spec Phase 9/12).
- **No in-situ LST validation network:** weather-station air temperature (if used) provides context only — not direct validation of LST.

## 5. Reproducibility limits

- Google Earth Engine API behavior and dataset versions can change over time → pin collection IDs and record asset metadata in Phase 3.
- Local processing depends on the Python environment (GeoPandas/Rasterio/Xarray) → pinned dependencies and documented setup in Phase 1.

## 6. Summary statement

All results will be interpreted within these limits. Where a limitation cannot be mitigated, it is restated in the Phase 13 validation document and in the final research documentation (Phase 16).
