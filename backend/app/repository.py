from uuid import UUID

from psycopg import Connection


class CatalogRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    def products(self, limit: int, offset: int) -> list[dict]:
        return self.connection.execute(
            "SELECT id, name, price_kopecks FROM product ORDER BY id DESC LIMIT %s OFFSET %s",
            (limit, offset),
        ).fetchall()

    def product(self, product_id: int) -> dict | None:
        return self.connection.execute(
            "SELECT id, name, image_key, price_kopecks FROM product WHERE id = %s",
            (product_id,),
        ).fetchone()

    def telegram_product(self, chat_id: int, message_id: int) -> dict | None:
        return self.connection.execute(
            "SELECT id FROM product WHERE telegram_chat_id = %s AND telegram_message_id = %s",
            (chat_id, message_id),
        ).fetchone()

    def add_telegram_product(
        self, chat_id: int, message_id: int, name: str, image_key: str
    ) -> int:
        row = self.connection.execute(
            """INSERT INTO product (name, image_key, telegram_chat_id, telegram_message_id)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (telegram_chat_id, telegram_message_id)
               DO UPDATE SET telegram_message_id = EXCLUDED.telegram_message_id
               RETURNING id""",
            (name, image_key, chat_id, message_id),
        ).fetchone()
        return row["id"]

    def lock_cart(self, session_id: UUID) -> None:
        self.connection.execute(
            "SELECT id FROM customer_session WHERE id = %s FOR UPDATE", (session_id,)
        )

    def cart(self, session_id: UUID) -> list[dict]:
        return self.connection.execute(
            """SELECT p.id, p.name, p.price_kopecks, c.quantity FROM cart_item c
               JOIN product p ON p.id = c.product_id
               WHERE c.session_id = %s ORDER BY p.id""",
            (session_id,),
        ).fetchall()

    def set_quantity(self, session_id: UUID, product_id: int, quantity: int) -> None:
        if quantity == 0:
            self.connection.execute(
                "DELETE FROM cart_item WHERE session_id = %s AND product_id = %s",
                (session_id, product_id),
            )
        else:
            self.connection.execute(
                """INSERT INTO cart_item (session_id, product_id, quantity) VALUES (%s, %s, %s)
                   ON CONFLICT (session_id, product_id) DO UPDATE SET quantity = EXCLUDED.quantity""",
                (session_id, product_id, quantity),
            )

    def order_for_request(self, session_id: UUID, request_id: UUID) -> dict | None:
        return self.connection.execute(
            "SELECT id FROM customer_order WHERE session_id = %s AND request_id = %s",
            (session_id, request_id),
        ).fetchone()

    def create_order(
        self,
        order_id: UUID,
        session_id: UUID,
        request_id: UUID,
        name: str,
        contact: str,
        items: list[dict],
    ) -> None:
        self.connection.execute(
            """INSERT INTO customer_order (id, session_id, request_id, name, contact)
               VALUES (%s, %s, %s, %s, %s)""",
            (order_id, session_id, request_id, name, contact),
        )
        with self.connection.cursor() as cursor:
            cursor.executemany(
                """INSERT INTO order_item (order_id, product_id, name, quantity, price_kopecks)
                   VALUES (%s, %s, %s, %s, %s)""",
                [
                    (
                        order_id,
                        item["id"],
                        item["name"],
                        item["quantity"],
                        item["price_kopecks"],
                    )
                    for item in items
                ],
            )
        self.connection.execute(
            "DELETE FROM cart_item WHERE session_id = %s", (session_id,)
        )

    def order_summary(self, order_id: UUID) -> dict:
        return self.connection.execute(
            """SELECT %s::uuid AS id,
                      COALESCE(SUM(price_kopecks::bigint * quantity), 0)::bigint AS total_kopecks
               FROM order_item WHERE order_id = %s""",
            (order_id, order_id),
        ).fetchone()
