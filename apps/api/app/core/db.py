"""PostgreSQL/PostGIS connection handling (Supabase).

The API talks to Supabase through its Postgres connection string
(``SUPABASE_DB_URL``). PostGIS spatial queries run as plain SQL via
psycopg — the REST API (PostgREST) is not used for spatial work.
"""

import logging
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    """Whether a Supabase database connection string is configured."""
    return bool(settings.supabase_db_url)


@contextmanager
def connect():
    """Yield a PostGIS connection; raises if the DB URL is not configured."""
    if not is_configured():
        raise RuntimeError("SUPABASE_DB_URL is not configured")
    with psycopg.connect(settings.supabase_db_url, row_factory=dict_row) as conn:
        yield conn


def postgis_version() -> str | None:
    """Return the PostGIS version string, or None if the DB is unavailable."""
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT postgis_version();")
                row = cur.fetchone()
                return row["postgis_version"] if row else None
    except Exception as exc:  # noqa: BLE001 - surface any failure as "unavailable"
        logger.warning("PostGIS availability check failed: %s", exc)
        return None
