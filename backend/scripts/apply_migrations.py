"""Apply SQL migrations to the Supabase database.

Usage (from backend/):  venv/Scripts/python scripts/apply_migrations.py [file ...]
With no arguments, applies every supabase/migrations/*.sql in name order. There is no
tracking table, so pass only the files that haven't been applied yet.
"""

import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "supabase" / "migrations"


def main(names: list[str]) -> None:
    db_url = get_settings().SUPABASE_DB_URL
    if not db_url:
        sys.exit("SUPABASE_DB_URL is not set in backend/.env")

    files = [MIGRATIONS_DIR / n for n in names] if names else sorted(MIGRATIONS_DIR.glob("*.sql"))
    with psycopg.connect(db_url) as conn:
        for path in files:
            # One transaction per file: a failing file rolls back fully and stops the run.
            with conn.transaction():
                conn.execute(path.read_text(encoding="utf-8"))
            print(f"applied {path.name}")
        # Make PostgREST pick up new tables immediately.
        conn.execute("notify pgrst, 'reload schema'")


if __name__ == "__main__":
    main(sys.argv[1:])
