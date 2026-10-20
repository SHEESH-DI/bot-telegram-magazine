"""Интеграционные проверки с PostgreSQL/MinIO из compose, без подмен хранилища."""

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import catalog
from app.catalog import add_product
from app.db import connect
from app.main import create_app
from app.settings import settings


@pytest.fixture
def customer():
    with TestClient(create_app(), base_url=settings.public_url) as client:
        yield client


def session_id(customer):
    assert customer.get("/api/cart").status_code == 200
    return customer.cookies.get("catalog_session")


def product_id():
    photo = BytesIO()
    Image.new("RGB", (8, 8), "white").save(photo, format="JPEG")
    return add_product(-42, uuid4().int % (2**31), "Тестовый товар", photo.getvalue())


def test_repeated_telegram_message_creates_one_product():
    photo = BytesIO()
    Image.new("RGB", (8, 8), "white").save(photo, format="JPEG")
    message_id = uuid4().int % (2**31)
    with ThreadPoolExecutor(2) as pool:
        ids = list(
            pool.map(
                lambda _: add_product(-42, message_id, "Тест", photo.getvalue()),
                range(2),
            )
        )
    assert ids[0] == ids[1]


def test_cart_persists_between_api_instances(customer):
    session_id(customer)
    product = product_id()
    origin = {"origin": settings.public_url.rstrip("/")}
    result = customer.put(f"/api/cart/{product}", json={"quantity": 3}, headers=origin)
    assert result.status_code == 200
    with TestClient(create_app(), base_url=settings.public_url) as another:
        another.cookies.set("catalog_session", customer.cookies.get("catalog_session"))
        assert another.get("/api/cart").json()["items"][0]["quantity"] == 3
    with TestClient(create_app(), base_url=settings.public_url) as stranger:
        assert stranger.get("/api/cart").json()["items"] == []


def test_concurrent_checkout_is_idempotent(customer):
    session = session_id(customer)
    product = product_id()
    catalog.set_quantity(session, product, 2)
    key = uuid4()
    with ThreadPoolExecutor(2) as pool:
        orders = list(
            pool.map(
                lambda _: catalog.checkout(session, key, "Имя", "Контакт"), range(2)
            )
        )
    assert orders[0]["id"] == orders[1]["id"]
    assert orders[0]["total_kopecks"] == orders[1]["total_kopecks"] == 99800
    with connect() as conn:
        assert catalog.cart(session) == []
        items = conn.execute(
            "SELECT * FROM order_item WHERE order_id = %s", (orders[0]["id"],)
        ).fetchall()
    assert len(items) == 1 and items[0]["quantity"] == 2
    assert items[0]["price_kopecks"] == 49900
    with connect() as conn:
        conn.execute(
            "UPDATE product SET price_kopecks = 99900 WHERE id = %s", (product,)
        )
    assert catalog.checkout(session, key, "Имя", "Контакт")["total_kopecks"] == 99800


def test_invalid_orders_and_csrf(customer):
    session_id(customer)
    product = product_id()
    assert customer.put(f"/api/cart/{product}", json={"quantity": 1}).status_code == 403
    origin = {"origin": settings.public_url.rstrip("/")}
    assert (
        customer.put(
            f"/api/cart/{product}", json={"quantity": 100}, headers=origin
        ).status_code
        == 422
    )
    assert (
        customer.post(
            "/api/orders",
            json={"request_id": str(uuid4()), "name": "  ", "contact": "mail"},
            headers=origin,
        ).status_code
        == 422
    )
    assert (
        customer.post(
            "/api/orders",
            json={"request_id": str(uuid4()), "name": "Имя", "contact": "mail"},
            headers=origin,
        ).status_code
        == 409
    )


def test_photo_is_available_without_local_file(customer):
    product = product_id()
    result = customer.get(f"/api/products/{product}/image")
    assert result.status_code == 200
    assert result.headers["content-type"] == "image/jpeg"
    assert Image.open(BytesIO(result.content)).size == (8, 8)


def test_product_response_hides_storage_details(customer):
    product = product_id()
    response = customer.get(f"/api/products/{product}")
    assert response.status_code == 200
    assert set(response.json()) == {"id", "name", "price_kopecks"}
    assert customer.get("/api/products/-1").status_code == 404


def test_invalid_photo_does_not_create_product():
    from app.errors import InvalidInput

    message_id = uuid4().int % (2**31)
    with pytest.raises(InvalidInput):
        add_product(-42, message_id, "Broken photo", b"not a photo")
    assert catalog.product_from_message(-42, message_id) is None
