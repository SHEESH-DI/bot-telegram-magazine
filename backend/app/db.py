import psycopg
from psycopg.rows import dict_row

from app.settings import settings


def connect():
    # Соединение живёт в пределах операции; состояние пользователей только в БД.
    return psycopg.connect(
        settings.database_url, row_factory=dict_row, connect_timeout=5
    )
