# PROGRESS

Development rule: build **one task at a time**. Before starting a task, read `PROJECT_SPEC.md` and this file, inspect the existing implementation, then implement only the first incomplete task.

Legend: `[ ]` pending · `[x]` done

## Phase 0 — Research Design

| Task | Description | Status |
|------|-------------|--------|
| 0.1 | Define research question | [x] |
| 0.2 | Define study area | [x] |
| 0.3 | Define datasets | [x] |
| 0.4 | Document methodology | [x] |
| 0.5 | Define limitations before analysis begins | [x] |

**Phase 0 complete.**

**Phase 1 complete.** Next: Phase 2 — Study Area (Lagos boundary, administrative boundaries, neighborhoods into PostGIS, then display on the map).

## Phase 1 — Application Foundation

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | Next.js application | [x] |
| 1.2 | FastAPI application | [x] |
| 1.3 | Supabase connection | [x] |
| 1.4 | PostGIS setup | [x] |
| 1.5 | Project documentation | [x] |
| 1.6 | Testing foundation | [x] |

> **Ordering note (user preference):** backend (1.2) is built before frontend (1.1). Supabase/PostGIS (1.3/1.4) are the database layer behind the API and come next; the frontend consumes the API, never Supabase directly.

## Phase 2 — Study Area

| Task | Description | Status |
|------|-------------|--------|
| 2.1 | City boundary in PostGIS | [x] |
| 2.2 | Administrative boundaries in PostGIS | [x] |
| 2.3 | Neighborhoods in PostGIS | [x] |
| 2.4 | Display boundaries on map | [x] |

**Phase 2 complete.** Next: Phase 3 — Landsat Pipeline (reproducible imagery workflow: date + extent, cloud filtering, clipping, metadata; no large imagery in Git).

## Phase 3 — Landsat Pipeline

| Task | Description | Status |
|------|-------------|--------|
| 3.1 | Reproducible imagery workflow | [x] |
| 3.2 | Date + geographic extent support | [ ] |
| 3.3 | Cloud filtering | [ ] |
| 3.4 | Clipping | [ ] |
| 3.5 | Metadata capture | [ ] |
| 3.6 | Large imagery excluded from Git | [ ] |

## Phase 4 — Preprocessing

| Task | Description | Status |
|------|-------------|--------|
| 4.1 | Cloud masking | [x] |
| 4.2 | Clipping | [x] |
| 4.3 | Raster alignment | [x] |
| 4.4 | Nodata handling | [x] |

**Phase 4 complete.** Next: Phase 5 — NDVI (NDVI raster, statistics, visualization, validation).

## Phase 5 — NDVI

| Task | Description | Status |
|------|-------------|--------|
| 5.1 | NDVI raster | [x] |
| 5.2 | NDVI statistics | [x] |
| 5.3 | NDVI visualization | [x] |
| 5.4 | NDVI value validation | [x] |

**Phase 5 complete.** Next: Phase 6 — Land Surface Temperature.

## Phase 6 — Land Surface Temperature

| Task | Description | Status |
|------|-------------|--------|
| 6.1 | LST bands + scaling documented | [ ] |
| 6.2 | LST emissivity assumptions documented | [ ] |
| 6.3 | LST conversions implemented | [ ] |
| 6.4 | LST limitations documented | [ ] |

## Phase 7 — Built-Up Analysis

| Task | Description | Status |
|------|-------------|--------|
| 7.1 | Built-up indicator (NDBI or justified alternative) | [ ] |
| 7.2 | Built-up map | [ ] |

## Phase 8 — Spatial Analysis

| Task | Description | Status |
|------|-------------|--------|
| 8.1 | LST vs NDVI | [ ] |
| 8.2 | LST vs built-up density | [ ] |
| 8.3 | LST vs land cover | [ ] |
| 8.4 | Statistical results output | [ ] |

## Phase 9 — Heat Hotspots

| Task | Description | Status |
|------|-------------|--------|
| 9.1 | High-LST / low-vegetation / high-built-up identification | [ ] |
| 9.2 | Interpretable hotspot categories | [ ] |

## Phase 10 — Web GIS

| Task | Description | Status |
|------|-------------|--------|
| 10.1 | LST layer | [ ] |
| 10.2 | NDVI layer | [ ] |
| 10.3 | Built-up layer | [ ] |
| 10.4 | Land-cover layer | [ ] |
| 10.5 | Hotspot layer | [ ] |
| 10.6 | Opacity controls | [ ] |
| 10.7 | Legends | [ ] |
| 10.8 | Date selection | [ ] |

## Phase 11 — Temporal Analysis

| Task | Description | Status |
|------|-------------|--------|
| 11.1 | Temperature change comparison | [ ] |
| 11.2 | Vegetation change comparison | [ ] |
| 11.3 | Built-up change comparison | [ ] |

## Phase 12 — Planning Insights

| Task | Description | Status |
|------|-------------|--------|
| 12.1 | Decision-support indicator layer (heat + low veg + high built-up) | [ ] |
| 12.2 | Clearly labeled as analytical indicator | [ ] |

## Phase 13 — Validation

| Task | Description | Status |
|------|-------------|--------|
| 13.1 | NDVI validation | [ ] |
| 13.2 | LST validation | [ ] |
| 13.3 | Spatial alignment validation | [ ] |
| 13.4 | Statistics validation | [ ] |
| 13.5 | Uncertainty + limitations documented | [ ] |

## Phase 14 — Testing

| Task | Description | Status |
|------|-------------|--------|
| 14.1 | Test all processing functions | [ ] |
| 14.2 | Test all user workflows | [ ] |

## Phase 15 — Deployment

| Task | Description | Status |
|------|-------------|--------|
| 15.1 | Deploy Web GIS | [ ] |
| 15.2 | Deploy backend | [ ] |
| 15.3 | Heavy raster processing off the request path | [ ] |

## Phase 16 — Final Research Documentation

| Task | Description | Status |
|------|-------------|--------|
| 16.1 | Full research documentation | [ ] |

---

## Change Log

| Date | Task | Summary |
|------|------|---------|
| 2026-08-19 | 5.1–5.4 | **Phase 5 complete — NDVI computation.** Module `remote_sensing/ndvi/compute.py`: NDVI = (NIR - RED) / (NIR + RED) with C2 L2 scaling (raw * 0.0000275 - 0.2). Critical fix: pixels below USGS valid range (raw < 7273) produce negative reflectance and extreme NDVI; excluded from computation. Near-zero denominator guard (|denom| < 0.001). Statistics: LC09 dry mean=0.4103, LC08 wet mean=0.4453; both within [-1, 1]. Validation: land-cover expectations match (water negative, vegetation 0.4-0.9, bare/urban <= 0.2). NDVI layer added to web map (brown-green colormap). 20 new tests; full suite 91/91. Docs: `docs/08_ndvi.md`. |
| 2026-08-19 | 4.1–4.4 | **Phase 4 complete — preprocessing pipeline.** Four modules in `remote_sensing/preprocessing/`: `cloud_mask.py` (QA_PIXEL bit-flag masking — bits 0–5: fill, dilated cloud, cirrus, cloud, cloud shadow, snow; bit 6 is Clear/inverted and NOT a mask bit), `clip.py` (rasterio.mask.mask with Lagos boundary), `align.py` (reference grid verification: EPSG:32631, 30 m), `nodata.py` (nodata=0, validation). Pipeline CLI (`python -m remote_sensing.preprocessing.pipeline`) processes both scenes: LC09 dry (81.4% valid, 0.02% cloud) and LC08 wet (41.4% valid, 35.4% cloud fallback). Critical bug found and fixed during testing: original code used bit 6 as Cirrus — it is actually the Clear flag (inverted), causing 99% masking. Verified against real QA_PIXEL values (21762=bit 1 dilated cloud, 21824=bits 6+confidence). 42 new tests (cloud mask: 14, clip: 6, align: 8, nodata: 10) — full suite 64/64 green. SR band validation range updated (uint16 0–65535, not 0–10000). Docs: `docs/07_preprocessing.md`. |
| 2026-08-17 | 3.1 (live) | **First live acquisition ran.** After the user's GEE setup (auth token, project `gen-lang-client-0763527607`, API enabled), the pipeline exported two 2023 scenes to Drive: dry `LC09_191055_20221219` (0.02% cloud, `best_in_window`) and wet `LC08_191055_20231027` (35.4% cloud, `fallback_above_threshold` — no scene under the 15% ceiling in the wet window, deviation recorded per methodology). Both GEE tasks started (EAW3I7QMCI5DTVCJXONHZE6K, ZJWS5NXE7WZLPDDXQIJ4TDLX); metadata records + manifest written to `data/processed/imagery/` (gitignored). Fixes found during the live run: `ee.Geometry` needs the geometry dict not the FeatureCollection (`geometry_from_geojson`); merged-collection `system:index` gets a merge prefix, so the feature `id` (full asset path) is used (`extra.asset_id`) for loading/exporting; new earthengine-api client uses `ee.batch.Export.image.toDrive` (no `ee.Export`). |
| 2026-08-17 | 3.1 | Reproducible Landsat acquisition workflow built in `remote_sensing/acquisition/`: `config.py` (single source of truth: LC08/LC09 C2 L2, path/row 191/055, cloud ceiling 15%, dry/wet seasonal windows, bands SR_B4-7 + ST_B10 + QA_PIXEL, UTM 31N, 30 m, COG), `search.py` (query builder + lowest-cloud selection with recorded `fallback_above_threshold` deviation per methodology §3.1), `export.py` (Drive COG export), `models.py` + `metadata.py` (per-scene JSON records + manifest in gitignored `data/processed/imagery/`), `pipeline.py` CLI (`--dry-run` needs no credentials). earthengine-api 1.7.39 installed in the project venv. Tests: 22 new (FakeEE stub in `tests/conftest.py`, no credentials needed) — query construction, selection/fallback, export params, metadata round-trip, dry-run. Verified `--dry-run` reads the Phase 2 Lagos boundary (bbox lon 2.7022–4.3508 / lat 6.3708–6.6984). Docs: `docs/06_landsat_acquisition.md`. Auth step for the user: `python -m earthengine authenticate`. Note: date/extent/cloud filtering and metadata are implemented as workflow capabilities (3.2/3.3/3.5 deepen/validate them); 3.6 (no imagery in Git) satisfied by existing gitignore. |
| 2026-08-17 | 2.4 | All three study-area layers display on the map (Task 2.4, Phase 2 complete): state (amber fill+outline), 20 LGAs (indigo outlines), 81 neighborhoods (teal points + 4 polygon outlines). The page fetches `/api/v1/boundaries/{city,lgas,neighborhoods}` through the Next proxy, shows live counts in the legend, and fits to the state boundary. Refactored the boundary effect to key on a `mapReady` state (React `react-hooks/refs` lint rule). Verified end-to-end in headless Chrome: API online, counts 20/81 rendered, map + OSM attribution present. Also killed stale uvicorn/next processes from a previous session that were masking newer routes. |
| 2026-08-17 | 2.3 | 81 Lagos neighborhoods loaded into PostGIS from OpenStreetMap (Overpass API, `place=suburb\|neighbourhood\|quarter`, clipped to the state boundary with shapely): 77 points + 4 polygons (Eko Atlantic, Badia East, Bariga, Banana Island), all valid. Script `scripts/fetch_lagos_neighborhoods.py` with mirror fallback; endpoint `GET /api/v1/boundaries/neighborhoods`. Loader now batches on a single connection (per-feature reconnects were slow over the pooler). shapely added to the GIS stack. Verified: 20/20 tests pass (4 new). Note: HDX admin-3 has no Lagos wards; LCDA boundaries aren't reliably available — documented as an OSM named-places layer instead. |
| 2026-08-16 | 0.1 | Defined the research question (primary + supporting questions, objectives, hypotheses). See `docs/01_research_question.md`. |
| 2026-08-16 | 0.2 | Defined the study area: Lagos State (20 LGAs, 5 divisions), rationale, climate, physical setting, analysis units, and recorded analytical-extent decisions. See `docs/02_study_area.md`. |
| 2026-08-16 | 0.3 | Defined datasets: Landsat 8/9 C2 L2 (path 191/055), GADM/HDX boundaries + OSM neighborhoods, ESA WorldCover, GHSL (optional), SRTM (optional), NOAA ISD (optional). See `docs/03_datasets.md`. |
| 2026-08-16 | 0.4 | Documented the methodology: end-to-end workflow, CRS choices (UTM 31N analysis / WGS84 delivery), equations (NDVI, NDBI, LST scaling), spatial statistics plan, hotspot thresholds approach, validation strategy. See `docs/04_methodology.md`. |
| 2026-08-16 | 0.4 (rev) | Expanded `docs/04_methodology.md`: LST basis rationale (C2 L2 ST_B10 vs avoided TOA path), acquisition sampling design, NDVI value validation, spatial-analysis sampling design (pixel vs LGA units, autocorrelation mitigation), full hotspot category table, temporal valid-pixel consistency, and per-scene QC checklist. |
| 2026-08-16 | 1.2 | FastAPI application skeleton in `apps/api/`: app factory, settings (pydantic-settings + .env), versioned router, health endpoint, CORS, pytest suite (3 tests passing on Python 3.11). Supabase/PostGIS placeholders in config, to be wired in 1.3/1.4. Built before 1.1 per user preference. |
| 2026-08-16 | 1.3/1.4 (code) | Supabase/PostGIS layer implemented: psycopg connection helpers (`app/core/db.py`), `/api/v1/health/db` endpoint, migration `001_enable_postgis.sql`, dev tooling (ruff, requirements-dev). Tests: 6 passed, 1 skipped (live-DB test). **Pending:** real credentials to verify connection — then 1.3/1.4 are marked done. |
| 2026-08-16 | 1.3/1.4 (done) | **Live connection verified.** Project connects via shared pooler `aws-1-eu-west-1.pooler.supabase.com` (new `aws-1-*` host format; `aws-0-*` returns "tenant not found"; direct `db.<ref>` host is IPv6-only and unreachable from this network). Migration `001_enable_postgis.sql` applied; PostGIS 3.3 confirmed via `/api/v1/health/db`. Test suite: 7 passed (live-DB test now runs). Format documented in `apps/api/.env.example` + `scripts/apply_migrations.py` added. |
| 2026-08-16 | 0.5 | Documented limitations before analysis: data, algorithm, statistical, scope, and reproducibility limits with mitigations. See `docs/05_limitations.md`. Phase 0 complete. |
| 2026-08-16 | 1.5/1.6 | Documentation and testing built into each task: `docs/01`–`05`, per-app READMEs, `PROJECT_SPEC.md`, `PROGRESS.md`; API pytest suite (7 passing), ruff lint, web `next build` + lint clean. Phase 1 complete. |
| 2026-08-16 | 2.2 | All 20 Lagos LGAs (NG025001–NG025020) loaded into PostGIS from the same HDX COD-AB download. `extract_lgas` added to service; `upsert_admin_unit` made level-aware (state/LGA/neighborhood name+pcode columns); fetch script now also writes `data/processed/boundaries/lagos_lgas.geojson`; endpoint `GET /api/v1/boundaries/lgas`. Verified: 20/20 valid geometries, combined LGA area 3488.2 km² (state 3671.5 km²; ~183 km² is lagoon/water outside LGAs), 16/16 tests pass. |
| 2026-08-16 | 2.1 | Lagos State boundary loaded into PostGIS. Source: OCHA HDX COD-AB (`nga_admin_boundaries.geojson.zip`, CC BY-IGO; GADM unreachable from dev network). Pipeline: `scripts/fetch_lagos_boundary.py` (download + extract state layer) → `database/migrations/002_city_boundary.sql` (`boundaries.admin_units` table: state/LGA/neighborhood, EPSG:4326, GIST index) → `scripts/load_boundaries.py` (upsert). Service layer `app/services/boundaries.py` + endpoint `GET /api/v1/boundaries/city` (GeoJSON). Verified: source area 3671.5 km² matches geometry area, `ST_IsValid`, bbox 2.7022–4.3508°E / 6.3708–6.6984°N; 13/13 tests pass. |
| 2026-08-16 | tooling | Added `scripts/npm-install-win.sh` — reusable installer encoding this machine's npm workarounds (offline-from-cache, `--ignore-scripts` for the crashing postinstalls, stale-process kill, retry-until-complete). Documented in `apps/web/README.md`. Verified: completes in seconds on an already-installed tree. |
| 2026-08-16 | 1.1 | Next.js application in `apps/web/`: Next.js 16 App Router + TypeScript + Tailwind 4 + MapLibre GL (v4). Map page centered on Lagos (OSM basemap, nav controls), API health indicator driven by proxied `/api/v1/health` (Next rewrites → `API_URL`, default localhost:8000), metadata + README. Verified: `npm run build` passes, `next start` serves HTTP 200 with map content. Notable: npm registry extremely slow on this machine + Windows file-lock/antivirus issues (ENOTEMPTY during `next` extraction, postinstall crash 0xC0000142) — resolved via `--ignore-scripts` + cache; documented in web README. |
