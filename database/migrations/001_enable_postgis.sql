-- Task 1.4 — Enable PostGIS on the Supabase Postgres instance.
--
-- How to run: open the Supabase Dashboard → SQL Editor, paste, and Run.
-- (or: psql "$SUPABASE_DB_URL" -f database/migrations/001_enable_postgis.sql)
--
-- Supabase ships PostGIS as an available extension; this migration makes
-- sure it is enabled and records the version for the project log.

CREATE EXTENSION IF NOT EXISTS postgis;

-- Confirm with:
-- SELECT postgis_version();
