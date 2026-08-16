# URBAN HEAT INTELLIGENCE

## PERSONAL PROJECT CONTEXT

This is my personal Geoinformatics and Remote Sensing project.

The goal is to build a Web GIS application that investigates Urban Heat Island patterns within a selected Nigerian city.

The initial study area should preferably be Lagos, Nigeria.

The application should combine:

* satellite imagery
* Land Surface Temperature
* NDVI
* built-up density
* land cover
* administrative boundaries

The final product should help answer:

> Which areas experience greater surface heat, and how is that related to vegetation and urban development?

This should demonstrate:

* Remote sensing
* Raster analysis
* GIS
* Python
* Web GIS
* PostGIS
* spatial statistics
* satellite data processing

---

# DEVELOPMENT RULES

Build one task at a time.

Before every task:

1. Read `PROJECT_SPEC.md`.
2. Read `PROGRESS.md`.
3. Inspect existing implementation.
4. Determine the first incomplete task.
5. Implement only that task.
6. Test it.
7. Explain what was done.
8. Update documentation.
9. Update `PROGRESS.md`.
10. Commit the work.
11. Stop.

Never silently skip tasks.

---

# TECHNOLOGY

Frontend:

* Next.js
* TypeScript
* Tailwind
* MapLibre

Backend:

* FastAPI
* Python

GIS:

* GeoPandas
* Rasterio
* NumPy
* Shapely
* Xarray

Remote sensing:

* Landsat
* Google Earth Engine where appropriate

Database:

* Supabase
* PostgreSQL
* PostGIS

Deployment:

* Vercel
* Render/Railway
* Supabase

NO DOCKER.

---

# PROJECT STRUCTURE

```text
urban-heat-intelligence/

├── apps/
│   ├── web/
│   └── api/

├── remote_sensing/
│   ├── acquisition/
│   ├── preprocessing/
│   ├── ndvi/
│   ├── lst/
│   └── builtup/

├── analysis/
│   ├── statistics/
│   └── hotspots/

├── data/
├── database/
│   └── migrations/
├── scripts/
├── tests/
├── docs/
├── PROJECT_SPEC.md
├── PROGRESS.md
└── README.md
```

---

# PHASE 0 — RESEARCH DESIGN

## Task 0.1

Define research question.

## Task 0.2

Define study area.

## Task 0.3

Define datasets.

## Task 0.4

Document methodology.

## Task 0.5

Define limitations before analysis begins.

---

# PHASE 1 — APPLICATION FOUNDATION

Create:

* Next.js application
* FastAPI application
* Supabase connection
* PostGIS
* project documentation
* testing

---

# PHASE 2 — STUDY AREA

Create:

* city boundary
* administrative boundaries
* neighborhoods

Store geometries in PostGIS.

Display them on the map.

---

# PHASE 3 — LANDSAT PIPELINE

Create reproducible imagery workflow.

Support:

* date
* geographic extent
* cloud filtering
* clipping
* metadata

Do not commit huge imagery files to Git.

---

# PHASE 4 — PREPROCESSING

Implement:

* cloud masking
* clipping
* raster alignment
* nodata handling

Document every step.

---

# PHASE 5 — NDVI

Implement:

```text
NDVI = (NIR - RED) / (NIR + RED)
```

Generate:

* NDVI raster
* statistics
* visualization

Validate values.

---

# PHASE 6 — LAND SURFACE TEMPERATURE

Implement a defensible Landsat LST methodology.

Document:

* bands
* scaling
* emissivity assumptions
* conversions
* limitations

Do not invent formulas or accuracy values.

---

# PHASE 7 — BUILT-UP ANALYSIS

Implement NDBI or another justified built-up indicator.

Generate built-up map.

---

# PHASE 8 — SPATIAL ANALYSIS

Analyze:

```text
LST vs NDVI
LST vs built-up density
LST vs land cover
```

Generate statistical results.

---

# PHASE 9 — HEAT HOTSPOTS

Identify:

* high LST
* low vegetation
* high built-up density

Create interpretable hotspot categories.

Do not describe them as health-risk zones without appropriate health data.

---

# PHASE 10 — WEB GIS

Implement:

* LST layer
* NDVI layer
* built-up layer
* land-cover layer
* hotspot layer
* opacity controls
* legends
* date selection

---

# PHASE 11 — TEMPORAL ANALYSIS

Compare dates.

Allow users to see:

* temperature change
* vegetation change
* built-up change

---

# PHASE 12 — PLANNING INSIGHTS

Create a decision-support layer identifying areas where:

```text
High heat
+
Low vegetation
+
High built-up intensity
```

suggests priority for further investigation/planning.

Clearly label this as an analytical indicator.

---

# PHASE 13 — VALIDATION

Validate:

* NDVI
* LST
* spatial alignment
* statistics

Document uncertainty and limitations.

---

# PHASE 14 — TESTING

Test all processing functions and user workflows.

---

# PHASE 15 — DEPLOYMENT

Deploy the Web GIS and backend.

Heavy raster processing must not block API requests.

---

# PHASE 16 — FINAL RESEARCH DOCUMENTATION

Document:

* research question
* study area
* data
* methodology
* equations
* processing
* results
* validation
* limitations
* future research

The final GitHub repository should look like a serious Geoinformatics research/software project.
