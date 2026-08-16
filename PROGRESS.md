# PROGRESS

Development rule: build **one task at a time**. Before starting a task, read `PROJECT_SPEC.md` and this file, inspect the existing implementation, then implement only the first incomplete task.

Legend: `[ ]` pending · `[x]` done

## Phase 0 — Research Design

| Task | Description | Status |
|------|-------------|--------|
| 0.1 | Define research question | [x] |
| 0.2 | Define study area | [ ] |
| 0.3 | Define datasets | [ ] |
| 0.4 | Document methodology | [ ] |
| 0.5 | Define limitations before analysis begins | [ ] |

## Phase 1 — Application Foundation

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | Next.js application | [ ] |
| 1.2 | FastAPI application | [ ] |
| 1.3 | Supabase connection | [ ] |
| 1.4 | PostGIS setup | [ ] |
| 1.5 | Project documentation | [ ] |
| 1.6 | Testing foundation | [ ] |

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
