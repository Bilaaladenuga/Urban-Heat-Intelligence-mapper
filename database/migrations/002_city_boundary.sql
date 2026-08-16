-- Task 2.1 — Study area boundaries schema.
--
-- One table holds every administrative unit we load (state, LGA,
-- neighborhood) so later phases (2.2, 2.3) reuse this migration rather
-- than forking tables. Geometries are stored in EPSG:4326 (WGS84), the
-- delivery CRS chosen in the methodology; rasters get reprojected for
-- analysis in EPSG:32631.
--
-- How to run: Supabase Dashboard → SQL Editor → paste → Run
-- (or: python scripts/apply_migrations.py)

CREATE SCHEMA IF NOT EXISTS boundaries;

CREATE TABLE IF NOT EXISTS boundaries.admin_units (
    id          BIGSERIAL PRIMARY KEY,
    level       TEXT NOT NULL CHECK (level IN ('state', 'lga', 'neighborhood')),
    name        TEXT NOT NULL,
    pcode       TEXT,                 -- e.g. NG025 (Lagos State)
    area_sqkm   NUMERIC,
    source      TEXT NOT NULL,        -- e.g. 'ocha_hdx_codab_v01'
    attributes  JSONB NOT NULL DEFAULT '{}'::jsonb,  -- full source properties
    geom        GEOMETRY(Geometry, 4326) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (level, name)
);

CREATE INDEX IF NOT EXISTS idx_admin_units_geom
    ON boundaries.admin_units USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_admin_units_level
    ON boundaries.admin_units (level);
