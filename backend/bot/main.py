import secrets
from contextlib import asynccontextmanager

from aiogram import Bot
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import ValidationError

from app.settings import settings
from bot.handlers import create_dispatcher
from bot.updates import process_once


def validate_settings() -> None:
    if (
        not settings.webhook_secret
        or settings.webhook_secret == "replace-with-random-secret"
    ):
        raise RuntimeError("Задайте случайный WEBHOOK_SECRET")
    if not settings.admins:
        raise RuntimeError("Задайте Telegram ID администратора в ADMIN_IDS")
    if not settings.public_url.startswith("https://"):
        raise RuntimeError("Telegram Mini App требует PUBLIC_URL с HTTPS")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.dispatcher = create_dispatcher()
    app.state.bot = None
    if settings.bot_token:
        validate_settings()
        app.state.bot = Bot(settings.bot_token)
    try:
        yield
    finally:
        if app.state.bot:
            await app.state.bot.session.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Бот каталога", lifespan=lifespan)

    @app.get("/health")
    def health():
        return {"status": "ok", "telegram_configured": bool(settings.bot_token)}

    @app.post("/telegram/webhook")
    async def webhook(
        request: Request, x_telegram_bot_api_secret_token: str = Header(default="")
    ):
        if not settings.webhook_secret or not secrets.compare_digest(
            x_telegram_bot_api_secret_token, settings.webhook_secret
        ):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Неверный секрет webhook")
        if not request.app.state.bot:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Бот не настроен")
        if len(body := await request.body()) > 1024 * 1024:
            raise HTTPException(
                status.HTTP_413_CONTENT_TOO_LARGE, "Обновление слишком большое"
            )
        try:
            update = Update.model_validate_json(body)
        except ValidationError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "Некорректное обновление Telegram",
            ) from exc
        await process_once(
            update.update_id,
            lambda: request.app.state.dispatcher.feed_update(
                request.app.state.bot, update
            ),
        )
        return {"ok": True}

    return app


app = create_app()
