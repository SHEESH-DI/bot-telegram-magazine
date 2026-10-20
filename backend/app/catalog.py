from uuid import UUID, uuid4

from app import storage
from app.db import connect
from app.errors import Conflict, InvalidInput, NotFound
from app.repository import CatalogRepository


def products(limit: int, offset: int) -> list[dict]:
    with connect() as connection:
        return CatalogRepository(connection).products(limit, offset)


def product(product_id: int) -> dict:
    with connect() as connection:
        row = CatalogRepository(connection).product(product_id)
    if row is None:
        raise NotFound("Товар не найден")
    return row


def product_from_message(chat_id: int, message_id: int) -> int | None:
    with connect() as connection:
        row = CatalogRepository(connection).telegram_product(chat_id, message_id)
    return row["id"] if row else None


def add_product(chat_id: int, message_id: int, name: str, photo: bytes) -> int:
    name = name.strip()
    if not 1 <= len(name) <= 200:
        raise InvalidInput("Название должно содержать от 1 до 200 символов")
    if existing := product_from_message(chat_id, message_id):
        return existing
    key = f"telegram/{chat_id}/{message_id}.jpg"
    storage.save_photo(key, photo)
    with connect() as connection:
        return CatalogRepository(connection).add_telegram_product(
            chat_id, message_id, name, key
        )


def cart(session_id: UUID) -> list[dict]:
    with connect() as connection:
        return CatalogRepository(connection).cart(session_id)


def set_quantity(session_id: UUID, product_id: int, quantity: int) -> list[dict]:
    if not 0 <= quantity <= 99:
        raise InvalidInput("Количество должно быть от 0 до 99")
    with connect() as connection:
        repository = CatalogRepository(connection)
        repository.lock_cart(session_id)
        if repository.product(product_id) is None:
            raise NotFound("Товар не найден")
        repository.set_quantity(session_id, product_id, quantity)
        return repository.cart(session_id)


def checkout(session_id: UUID, request_id: UUID, name: str, contact: str) -> dict:
    name, contact = name.strip(), contact.strip()
    if not 1 <= len(name) <= 200 or not 1 <= len(contact) <= 300:
        raise InvalidInput("Укажите имя и контакт для связи")
    with connect() as connection:
        repository = CatalogRepository(connection)
        # Изменение корзины и оформление заказа используют один замок сессии.
        repository.lock_cart(session_id)
        if existing := repository.order_for_request(session_id, request_id):
            return repository.order_summary(existing["id"])
        items = repository.cart(session_id)
        if not items:
            raise Conflict("Корзина пуста")
        order_id = uuid4()
        repository.create_order(order_id, session_id, request_id, name, contact, items)
        return repository.order_summary(order_id)
