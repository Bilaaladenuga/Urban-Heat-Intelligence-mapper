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
| LCDAs / neighborhoods | 37 | Finer display layer; neighborhood-level insights (Phase 2) |

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

- Source of the official boundary (GADM vs OCHA/HDX) — decided in Phase 2 when the geometry is loaded into PostGIS.
- Final confirmation of the exact bounding box from the chosen boundary dataset.
