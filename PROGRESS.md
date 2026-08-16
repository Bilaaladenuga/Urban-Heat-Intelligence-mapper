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
| 2.1 | City boundary in PostGIS | [ ] |
| 2.2 | Administrative boundaries in PostGIS | [ ] |
| 2.3 | Neighborhoods in PostGIS | [ ] |
| 2.4 | Display boundaries on map | [ ] |

## Phase 3 — Landsat Pipeline

| Task | Description | Status |
|------|-------------|--------|
| 3.1 | Reproducible imagery workflow | [ ] |
| 3.2 | Date + geographic extent support | [ ] |
| 3.3 | Cloud filtering | [ ] |
| 3.4 | Clipping | [ ] |
| 3.5 | Metadata capture | [ ] |
| 3.6 | Large imagery excluded from Git | [ ] |

## Phase 4 — Preprocessing

| Task | Description | Status |
|------|-------------|--------|
| 4.1 | Cloud masking | [ ] |
| 4.2 | Clipping | [ ] |
| 4.3 | Raster alignment | [ ] |
| 4.4 | Nodata handling | [ ] |

## Phase 5 — NDVI

| Task | Description | Status |
|------|-------------|--------|
| 5.1 | NDVI raster | [ ] |
| 5.2 | NDVI statistics | [ ] |
| 5.3 | NDVI visualization | [ ] |
| 5.4 | NDVI value validation | [ ] |

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
| 2026-08-16 | 1.1 | Next.js application in `apps/web/`: Next.js 16 App Router + TypeScript + Tailwind 4 + MapLibre GL (v4). Map page centered on Lagos (OSM basemap, nav controls), API health indicator driven by proxied `/api/v1/health` (Next rewrites → `API_URL`, default localhost:8000), metadata + README. Verified: `npm run build` passes, `next start` serves HTTP 200 with map content. Notable: npm registry extremely slow on this machine + Windows file-lock/antivirus issues (ENOTEMPTY during `next` extraction, postinstall crash 0xC0000142) — resolved via `--ignore-scripts` + cache; documented in web README. |
