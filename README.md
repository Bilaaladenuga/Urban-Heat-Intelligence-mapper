# Urban Heat Intelligence

A Web GIS application investigating **Urban Heat Island patterns in Lagos, Nigeria** using Landsat satellite imagery, Land Surface Temperature (LST), NDVI, built-up density, and land cover — built on Next.js, FastAPI, and PostGIS.

> **Research question:** Which areas experience greater surface heat, and how is that related to vegetation and urban development?

This is a personal Geoinformatics and Remote Sensing project demonstrating remote sensing, raster analysis, GIS, Python, Web GIS, PostGIS, spatial statistics, and satellite data processing.

## Repository layout

```text
apps/            Next.js web app + FastAPI backend
remote_sensing/  acquisition, preprocessing, NDVI, LST, built-up pipelines
analysis/        spatial statistics and hotspot analysis
data/            local data (rasters never committed to Git)
database/        migrations
scripts/         one-off and automation scripts
tests/           automated tests
docs/            research design and technical documentation
```

## Getting started

Not yet — the project is in **Phase 0 (Research Design)**. See `PROJECT_SPEC.md` for the full plan and `PROGRESS.md` for current status.

## Development rules

See `PROJECT_SPEC.md` → Development Rules. One task at a time; `PROGRESS.md` tracks state.
