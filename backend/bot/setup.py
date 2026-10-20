import asyncio

from aiogram import Bot
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from app.settings import settings


async def main():
    if not settings.bot_token or not settings.public_url.startswith("https://"):
        raise SystemExit("Нужны BOT_TOKEN и публичный HTTPS PUBLIC_URL")
    if (
        not settings.webhook_secret
        or settings.webhook_secret == "replace-with-random-secret"
    ):
        raise SystemExit("Задайте случайный WEBHOOK_SECRET")
    async with Bot(settings.bot_token) as bot:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Открыть каталог"),
                BotCommand(
                    command="create", description="Создать товар (для администратора)"
                ),
            ]
        )
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Каталог", web_app=WebAppInfo(url=settings.public_url)
            )
        )
        await bot.set_webhook(
            settings.public_url.rstrip("/") + "/telegram/webhook",
            secret_token=settings.webhook_secret,
            allowed_updates=["message"],
            drop_pending_updates=False,
        )
        print("Webhook и меню настроены")


if __name__ == "__main__":
    asyncio.run(main())
