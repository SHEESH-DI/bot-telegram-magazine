"""Запускает интеграционные проверки отдельно от каталога демонстрации."""

from urllib.parse import urlsplit, urlunsplit

import pytest

from app.db import connect
from app.migrate import main as migrate
from app.settings import settings


def main():
    with connect() as conn:
        conn.commit()
        conn.autocommit = True
        if not conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = 'catalog_test'"
        ).fetchone():
            conn.execute("CREATE DATABASE catalog_test")
    parts = urlsplit(settings.database_url)
    settings.database_url = urlunsplit(parts._replace(path="/catalog_test"))
    settings.s3_bucket += "-test"
    migrate()
    raise SystemExit(
        pytest.main(["tests", "-q", "--capture=sys", "-p", "no:cacheprovider"])
    )


if __name__ == "__main__":
    main()
