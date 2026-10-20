from collections.abc import Awaitable, Callable

import psycopg

from app.settings import settings


async def process_once(
    update_id: int, handler: Callable[[], Awaitable[object]]
) -> bool:
    async with await psycopg.AsyncConnection.connect(
        settings.database_url, connect_timeout=5
    ) as connection:
        # Две реплики могут получить одно обновление одновременно.
        await connection.execute("SET LOCAL lock_timeout = '20s'")
        await connection.execute("SELECT pg_advisory_xact_lock(%s)", (update_id,))
        cursor = await connection.execute(
            "SELECT 1 FROM telegram_update WHERE update_id = %s", (update_id,)
        )
        if await cursor.fetchone():
            return False
        await handler()
        await connection.execute(
            "INSERT INTO telegram_update (update_id) VALUES (%s)", (update_id,)
        )
    return True
