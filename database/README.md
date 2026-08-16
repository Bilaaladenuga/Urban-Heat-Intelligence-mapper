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
- Phase 2 will add the boundaries schema (state, LGAs, neighborhoods).
