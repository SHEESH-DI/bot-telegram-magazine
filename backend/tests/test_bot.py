import asyncio
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from aiogram import Bot
from aiogram.types import Message, Update
from fastapi.testclient import TestClient
from PIL import Image

from app import catalog
from app.settings import settings
from bot.handlers import create, create_dispatcher, photo
from bot.main import create_app


def test_admin_access_and_caption(monkeypatch):
    monkeypatch.setattr(settings, "admin_ids", "123")
    answer = AsyncMock()
    outsider = SimpleNamespace(from_user=SimpleNamespace(id=456), answer=answer)
    asyncio.run(create(outsider))
    assert "только администратор" in answer.call_args.args[0]

    answer.reset_mock()
    admin = SimpleNamespace(
        from_user=SimpleNamespace(id=123), caption=" ", answer=answer
    )
    asyncio.run(photo(admin, AsyncMock()))
    assert "название" in answer.call_args.args[0]


def test_webhook_secret_and_duplicate_delivery(monkeypatch):
    monkeypatch.setattr(settings, "bot_token", "123456:" + "a" * 35)
    monkeypatch.setattr(settings, "admin_ids", "123")
    monkeypatch.setattr(settings, "public_url", "https://catalog.example")
    monkeypatch.setattr(settings, "webhook_secret", "test-webhook-secret")
    update = {"update_id": uuid4().int % (2**60)}
    first, second = create_app(), create_app()
    with TestClient(first) as client, TestClient(second) as another:
        calls = AsyncMock()
        monkeypatch.setattr(first.state.dispatcher, "feed_update", calls)
        monkeypatch.setattr(second.state.dispatcher, "feed_update", calls)
        assert client.post("/telegram/webhook", json=update).status_code == 403

        def deliver(target):
            return target.post(
                "/telegram/webhook",
                json=update,
                headers={"X-Telegram-Bot-Api-Secret-Token": "test-webhook-secret"},
            ).status_code

        with ThreadPoolExecutor(2) as pool:
            assert list(pool.map(deliver, [client, another])) == [200, 200]
        assert calls.await_count == 1


def test_failed_update_can_be_retried():
    from bot.updates import process_once

    update_id = uuid4().int % (2**60)
    handler = AsyncMock(side_effect=[RuntimeError("Temporary failure"), None])
    import pytest

    with pytest.raises(RuntimeError):
        asyncio.run(process_once(update_id, handler))
    assert asyncio.run(process_once(update_id, handler)) is True
    assert asyncio.run(process_once(update_id, handler)) is False
    assert handler.await_count == 2


@pytest.mark.parametrize("media", ["video", "animation", "document", "video_note"])
def test_unsupported_media_is_not_treated_as_start(monkeypatch, media):
    monkeypatch.setattr(settings, "admin_ids", "123")
    payload = {
        "file_id": "file",
        "file_unique_id": "unique",
        "width": 32,
        "height": 32,
        "length": 32,
        "duration": 1,
    }
    update = Update.model_validate(
        {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "date": 1700000000,
                "chat": {"id": 123, "type": "private"},
                "from": {"id": 123, "is_bot": False, "first_name": "Admin"},
                "caption": "Название товара",
                media: payload,
            },
        }
    )
    session = AsyncMock(
        return_value=Message.model_validate(
            {
                "message_id": 2,
                "date": 1700000000,
                "chat": {"id": 123, "type": "private"},
                "text": "Ответ",
            }
        )
    )
    bot = Bot("123456:" + "a" * 35, session=session)
    asyncio.run(create_dispatcher().feed_update(bot, update))
    assert session.await_count == 1
    request = session.await_args.args[1]
    assert "Товар не создан" in request.text
    assert "фотографи" in request.text


def test_photo_with_caption_creates_product(monkeypatch):
    monkeypatch.setattr(settings, "admin_ids", "123")
    message_id = uuid4().int % (2**31)
    update = Update.model_validate(
        {
            "update_id": message_id,
            "message": {
                "message_id": message_id,
                "date": 1700000000,
                "chat": {"id": -42, "type": "private"},
                "from": {"id": 123, "is_bot": False, "first_name": "Admin"},
                "caption": "Фото из бота",
                "photo": [
                    {
                        "file_id": "photo",
                        "file_unique_id": "unique",
                        "width": 8,
                        "height": 8,
                    }
                ],
            },
        }
    )
    photo = BytesIO()
    Image.new("RGB", (8, 8), "white").save(photo, format="JPEG")
    session = AsyncMock(
        return_value=Message.model_validate(
            {
                "message_id": 2,
                "date": 1700000000,
                "chat": {"id": -42, "type": "private"},
                "text": "Ответ",
            }
        )
    )
    bot = Bot("123456:" + "a" * 35, session=session)
    monkeypatch.setattr(
        bot,
        "download",
        AsyncMock(
            side_effect=lambda image, destination: destination.write(photo.getvalue())
        ),
    )
    asyncio.run(create_dispatcher().feed_update(bot, update))
    product_id = catalog.product_from_message(-42, message_id)
    assert product_id is not None
    assert catalog.product(product_id)["name"] == "Фото из бота"
    assert "создан" in session.await_args.args[1].text
