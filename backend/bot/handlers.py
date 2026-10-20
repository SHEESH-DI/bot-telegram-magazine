import asyncio
from io import BytesIO

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from app import catalog
from app.errors import InvalidInput
from app.settings import settings
from app.storage import MAX_PHOTO_BYTES


def menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть каталог", web_app=WebAppInfo(url=settings.public_url)
                )
            ]
        ]
    )


async def create(message: Message) -> None:
    if not message.from_user or message.from_user.id not in settings.admins:
        await message.answer("Создавать товары может только администратор")
        return
    await message.answer(
        "Пришлите фотографию товара, а название укажите в подписи к ней — одним сообщением."
        " Видео и GIF пока не поддерживаются."
    )


async def photo(message: Message, bot: Bot) -> None:
    if not message.from_user or message.from_user.id not in settings.admins:
        await message.answer("У меня есть товар", reply_markup=menu())
        return
    name = (message.caption or "").strip()
    if not 1 <= len(name) <= 200:
        await message.answer("Добавьте к фото название длиной от 1 до 200 символов")
        return
    if message.media_group_id:
        await message.answer("Пришлите одно фото с названием, без альбома")
        return
    product_id = await asyncio.to_thread(
        catalog.product_from_message, message.chat.id, message.message_id
    )
    if product_id is None:
        image = message.photo[-1]
        if (image.file_size or 0) > MAX_PHOTO_BYTES:
            await message.answer("Фото должно быть не больше 10 МБ")
            return
        buffer = BytesIO()
        await bot.download(image, destination=buffer)
        try:
            product_id = await asyncio.to_thread(
                catalog.add_product,
                message.chat.id,
                message.message_id,
                name,
                buffer.getvalue(),
            )
        except InvalidInput as exc:
            await message.answer(str(exc))
            return
    await message.answer(f"Товар №{product_id} создан", reply_markup=menu())


async def start(message: Message) -> None:
    await message.answer("У меня есть товар", reply_markup=menu())
    if message.from_user and message.from_user.id in settings.admins:
        await message.answer("Добавить товар: /create или «Создать товар»")


async def unsupported_media(message: Message) -> None:
    if not message.from_user or message.from_user.id not in settings.admins:
        await start(message)
        return
    await message.answer(
        "Товар не создан: нужна обычная фотография с названием в подписи. "
        "Видео, GIF и файлы пока не поддерживаются."
    )


def create_dispatcher() -> Dispatcher:
    router = Router()
    router.message.register(create, Command("create"))
    router.message.register(create, F.text == "Создать товар")
    router.message.register(photo, F.photo)
    router.message.register(
        unsupported_media, F.video | F.animation | F.document | F.video_note
    )
    router.message.register(start)
    dispatcher = Dispatcher(disable_fsm=True)
    dispatcher.include_router(router)
    return dispatcher
