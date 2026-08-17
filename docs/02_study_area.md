# Task 0.2 — Study Area

**Status:** Complete (Phase 0 — Research Design)

## Study area: Lagos State, Nigeria

**Location:** Southwestern Nigeria, on the coast of the Gulf of Guinea (Bight of Benin).

**Approximate extent:** Lat 6.2°N – 6.7°N; Lon 2.7°E – 4.4°E. Exact bounds to be confirmed from the official boundary dataset in Phase 2.

**Landsat coverage:** WRS-2 path 191, row 055 — a single scene covers the entire state.

## Why Lagos?

1. **Scale of urbanization:** Nigeria's largest city and economic capital, and one of Africa's largest metropolitan areas. Rapid, largely informal urban expansion makes it a textbook Urban Heat Island setting.
2. **Land-cover contrast:** Dense built-up core (Lagos Island, Mainland, Ikeja) sits alongside the Lagos Lagoon, creeks, wetlands/mangroves, and peri-urban expansion (Ibeju-Lekki, Epe, Badagry). This gives a wide LST gradient to analyze.
3. **Coastal setting:** Extensive water bodies moderate temperatures and create strong thermal contrast with urban surfaces — an interesting and relevant feature for LST analysis (water masking is a documented decision in the methodology).
4. **Data availability:** Lagos has good Landsat coverage (fewer persistently cloudy scenes than parts of the Niger Delta), plus widely available boundary and land-cover datasets (GADM, OCHA/HDX, ESA WorldCover).
5. **Administrative granularity:** 5 divisions → 20 LGAs → 37 LCDAs provide multiple meaningful units for zonal statistics and neighborhood-level display.

## Administrative hierarchy (analysis units)

| Level | Count | Role in project |
|-------|-------|-----------------|
| Lagos State boundary | 1 | Primary AOI for raster clipping and map extent |
| Divisions | 5 | Context (Ikeja, Badagry, Ikorodu, Lagos Island, Epe) |
| Local Government Areas (LGAs) | 20 | Main unit for zonal statistics (LST/NDVI/built-up per LGA) |
| Neighborhoods (OSM named places) | 81 | Finer display layer; neighborhood-level context (Phase 2) |

> **Loaded (Task 2.2):** all 20 Lagos LGAs (pcodes NG025001–NG025020) in `boundaries.admin_units`, level `lga`, from the same HDX COD-AB source. Combined LGA area 3488.2 km² vs state 3671.5 km² — the ~183 km² difference is lagoon/water inside the state boundary but outside LGA polygons (consistent with the water-masking decision).
>
> **Loaded (Task 2.3):** 81 named neighborhoods (77 suburb/neighbourhood points + 4 polygon boundaries) from OpenStreetMap via the Overpass API, clipped to the state boundary. Stored at level `neighborhood`, source `osm_overpass`. Note: the earlier plan of 37 LCDAs was revised to OSM named places — LCDA boundaries are not published in the HDX COD-AB or reliably mapped in OSM; OSM `place=suburb|neighbourhood|quarter` provides a consistent, attributable display layer instead.
>
> **Displayed (Task 2.4):** all three layers (state, LGAs, neighborhoods) render on the map via `GET /api/v1/boundaries/{city,lgas,neighborhoods}` through the Next.js proxy; the legend shows live feature counts and the view fits to the state boundary.

## Climate context

- **Köppen classification:** Tropical wet-and-dry (Aw).
- **Seasons:** Dry season roughly November–March; wet season roughly April–October with a relatively drier period around August.
- **Implications for imagery:** Seasonal sampling of Landsat scenes (one dry-season and one wet-season acquisition) is planned for the temporal analysis (Phase 11). Cloud-free acquisitions are more likely in the dry season.

## Physical setting

- Low-lying, predominantly flat terrain (elevation context from SRTM, optional).
- Lagos Lagoon, Lekki Lagoon, and a network of creeks and wetlands dominate the southern half.
- Urban core on Lagos Island/Victoria Island and the Mainland; rapid eastward and westward peri-urban expansion.

## Analytical extent decisions (recorded now)

1. **AOI = Lagos State boundary** for all raster processing (clip in Phase 4).
2. **Water masking** to be applied for vegetation/built-up analyses where water pixels would distort statistics (documented decision; exact approach in Phase 4/8).
3. **Zonal statistics** aggregated at **LGA level** (20 units), with neighborhood level as a finer option.

## Open items (resolved in Phase 2)

- **Boundary source: OCHA HDX COD-AB** (`nga_admin_boundaries.geojson.zip`, CC BY-IGO) — GADM's server was unreachable from the development network; HDX worked and provides state + LGA + ward levels in one download. Loaded into PostGIS (Task 2.1): `boundaries.admin_units`, Lagos pcode `NG025`.
- **Confirmed bounding box** (from the loaded geometry, EPSG:4326): lon 2.7022–4.3508°E, lat 6.3708–6.6984°N. Source area 3671.5 km² matches the geometry-computed area; geometry passes `ST_IsValid`.
- **Neighborhoods (Task 2.3): OpenStreetMap via Overpass API** — `place = suburb | neighbourhood | quarter` queried within the state bbox, clipped to the Lagos boundary with shapely. 81 features loaded (77 points, 4 polygons). Script: `scripts/fetch_lagos_neighborhoods.py` (mirror fallback: overpass-api.de → kumi → mail.ru → osm.ch). License: ODbL (attribution recorded per feature: `osm_type`/`osm_id`).
