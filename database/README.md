# Database

Supabase (PostgreSQL + PostGIS). Migrations live in `database/migrations/`, numbered sequentially.

## Applying migrations

Option A — **Supabase Dashboard → SQL Editor**: paste the migration contents and run.

Option B — **psql** (local):

```bash
psql "$SUPABASE_DB_URL" -f database/migrations/001_enable_postgis.sql
```

The connection string (`SUPABASE_DB_URL`) lives in `apps/api/.env` (see `apps/api/.env.example`).

## Status

- `001_enable_postgis.sql` — enables the PostGIS extension (Task 1.4).
- `002_city_boundary.sql` — `boundaries` schema + `boundaries.admin_units` table (state/LGA/neighborhood geometries, EPSG:4326, GIST index) (Task 2.1).

## Loading study-area data (Phase 2)

```bash
cd apps/api
.venv/Scripts/python ../../scripts/fetch_lagos_boundary.py   # download + extract Lagos from HDX
.venv/Scripts/python ../../scripts/apply_migrations.py        # apply migrations
.venv/Scripts/python ../../scripts/load_boundaries.py         # upsert into PostGIS
```

Serve the boundary: `GET /api/v1/boundaries/city`.
