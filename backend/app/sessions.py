from uuid import UUID, uuid4

from app.db import connect

COOKIE_NAME = "catalog_session"
SESSION_MAX_AGE = 30 * 86400


def get_or_create(cookie: str | None) -> UUID:
    try:
        session_id = UUID(cookie or "")
    except ValueError:
        session_id = None
    with connect() as connection:
        if session_id:
            row = connection.execute(
                "SELECT id FROM customer_session WHERE id = %s AND expires_at > now()",
                (session_id,),
            ).fetchone()
            if row:
                return session_id
        session_id = uuid4()
        connection.execute(
            "INSERT INTO customer_session (id) VALUES (%s)", (session_id,)
        )
    return session_id
