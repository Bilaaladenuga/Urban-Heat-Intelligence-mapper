"""Apply database migrations in order.

Usage (from anywhere):
    python scripts/apply_migrations.py

Reads ``apps/api/.env`` for ``SUPABASE_DB_URL`` (see the project README).
Each migration in ``database/migrations/`` runs in its own transaction.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core import db  # noqa: E402


def main() -> None:
    if not db.is_configured():
        print("SUPABASE_DB_URL is not configured (check apps/api/.env). Aborting.")
        sys.exit(1)

    migrations = sorted((ROOT / "database" / "migrations").glob("*.sql"))
    if not migrations:
        print("No migrations found in database/migrations/.")
        return

    for path in migrations:
        sql = path.read_text(encoding="utf-8")
        with db.connect() as conn, conn.cursor() as cur:
            cur.execute(sql)
        print(f"applied  {path.name}")


if __name__ == "__main__":
    main()
