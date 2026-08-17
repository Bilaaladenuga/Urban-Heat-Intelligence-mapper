# Task 3.1 — Landsat Acquisition Workflow

**Status:** Complete (Phase 3 — Landsat Pipeline)

A reproducible workflow for searching, selecting, exporting and documenting
Landsat 8/9 Collection 2 Level-2 scenes for Lagos State, per the design in
`docs/04_methodology.md` §3.1 and `docs/03_datasets.md`.

## Workflow

```text
config.py (single source of truth)          search.py             export.py
───────────────────────────────    ──────────────────────   ─────────────────
collections, path/row 191/055  →   per seasonal window:    →  ee.batch.Export.image
cloud threshold (15%)              filter date/bounds/           .toDrive
seasonal windows (dry/wet)         path/row/cloud →             bands, region,
bands, scale, CRS, folder          best scene (fallback          UTM 31N, COG
                                   recorded as deviation)
                                            │
                                            ▼
                                   metadata.py → data/processed/imagery/
                                   {scene_id}.json + manifest.json (gitignored)
```

The pipeline is orchestrated by `remote_sensing/acquisition/pipeline.py`:

```bash
# Plan only (no Earth Engine calls, no credentials needed):
python -m remote_sensing.acquisition.pipeline --dry-run --year 2023

# Live run (requires one-time auth):
earthengine authenticate
python -m remote_sensing.acquisition.pipeline --year 2023

> **Windows note:** the Earth Engine CLI is an executable in the venv,
> `apps/api/.venv/Scripts/earthengine.exe` — `python -m earthengine` does
> **not** work (the import name is `ee`). Use the full path below (or
> activate the venv first so `earthengine` is on PATH):
>
> ```bash
> apps/api/.venv/Scripts/earthengine.exe authenticate
> ```
```

Run from the repository root with the project venv
(`apps/api/.venv/Scripts/python` on Windows).

## Selection rules (methodology §3.1)

- **Seasonal windows:** dry = Nov–Mar (crosses the year boundary),
  wet = Apr–Oct. One scene per window.
- **Cloud ceiling:** default 15 % (the methodology target is <10–20 %;
  the ceiling is overridable with `--cloud-threshold`).
- **Best scene:** lowest `CLOUD_COVER` within the ceiling.
- **Fallback:** if no scene meets the ceiling, the lowest-cloud scene in
  the window is used and the deviation is **recorded on the metadata
  record** (`selection = fallback_above_threshold`, `notes` explains why).
  A cloudy scene is never forced silently.
- **No scene available** in a window → recorded, no export for that window.

## What gets exported per scene

| Item | Value |
|------|-------|
| Bands | `SR_B4` (Red), `SR_B5` (NIR), `SR_B6` (SWIR1), `SR_B7` (SWIR2), `ST_B10` (surface temperature), `QA_PIXEL` |
| Resolution | 30 m |
| CRS | EPSG:32631 (UTM zone 31N — analysis grid per methodology §2) |
| Format | Cloud-Optimized GeoTIFF |
| Region | Lagos State boundary (`data/processed/boundaries/lagos_state.geojson`, Phase 2) |
| Destination | Google Drive folder `urban_heat_intelligence` |

## Downloading the exports

Once the GEE tasks finish, the cloud-optimized GeoTIFFs appear in the Drive
folder `urban_heat_intelligence/` (one file per band, named
`{scene_id}.{BAND}.tif`). Move them locally, one folder per scene, matching
the metadata records:

```text
data/raw/imagery/{scene_id}/   # e.g. data/raw/imagery/LC09_191055_20221219/
```

`data/raw/` is gitignored, so imagery is never committed. Phase 4
(preprocessing) reads these files.

## Metadata record (per scene)

Written to `data/processed/imagery/{scene_id}.json`, with a run manifest at
`data/processed/imagery/manifest.json`. Fields:

```text
scene_id, satellite, date, wrs_path, wrs_row, cloud_cover_pct,
window (dry/wet), selection (best_in_window | fallback_above_threshold),
source_collection, bands, crs, scale_meters, geometry_source,
cloud_above_threshold, notes (selection rationale), extra (product id,
export task id)
```

## Reproducibility guarantees

1. **One config file** (`remote_sensing/acquisition/config.py`) holds every
   tunable — the same inputs always produce the same query and selection.
2. **Deterministic selection:** the lowest-cloud rule and the recorded
   fallback leave no manual choice in the pipeline.
3. **Full provenance per scene:** every record carries the source
   collection, the exact bands/CRS/scale exported, the selection rule and
   any deviation — enough to re-run or audit any later product.
4. **No silent steps:** `--dry-run` prints the complete plan (windows,
   dates, geometry bbox, export parameters) before anything runs.
5. **Imagery never enters Git** (Task 3.6): exports land in Google Drive;
   local copies/metadata go to `data/processed/imagery/`, which is
   gitignored (`data/processed/`). Only code, config and docs are
   committed.

## One-time setup (your side)

```bash
pip install earthengine-api                  # already installed
apps/api/.venv/Scripts/earthengine.exe authenticate  # opens a browser
```

(`python -m earthengine` fails because the package imports as `ee`; the
CLI ships as the `earthengine` executable in the venv `Scripts` folder.)

The live run then exports scenes to the Drive folder
`urban_heat_intelligence/`; download them from Google Drive (or a future
script can pull them via the Drive API). Later phases (4–7) process the
downloaded COGs locally with rasterio/numpy.

## Tests

`tests/test_acquisition_*.py` — 22 tests covering window-date math, query
construction, record mapping, selection + fallback logic, export task
parameters, metadata persistence and the CLI dry-run. GEE is stubbed
(`tests/conftest.py::FakeEE`), so the suite runs without credentials.

```bash
python -m pytest tests/
```
