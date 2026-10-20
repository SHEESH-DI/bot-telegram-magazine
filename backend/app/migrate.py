from pathlib import Path

from app.db import connect
from app.settings import settings
from app.storage import client


def main():
    with connect() as conn:
        # Два одновременно запущенных migration job выполнят DDL последовательно.
        conn.execute("SELECT pg_advisory_xact_lock(728401)")
        conn.execute("""CREATE TABLE IF NOT EXISTS schema_migration (
            name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now()
        )""")
        for path in sorted(Path("migrations").glob("*.sql")):
            if conn.execute(
                "SELECT 1 FROM schema_migration WHERE name = %s", (path.name,)
            ).fetchone():
                continue
            conn.execute(path.read_text())
            conn.execute(
                "INSERT INTO schema_migration (name) VALUES (%s)", (path.name,)
            )
    s3 = client()
    if not s3.bucket_exists(settings.s3_bucket):
        s3.make_bucket(settings.s3_bucket)
    print("Схема и бакет готовы")


if __name__ == "__main__":
    main()
