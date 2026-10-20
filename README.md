# Каталог

Каталог товаров с Telegram-ботом: Next.js App Router, FastAPI, aiogram 3,
PostgreSQL и MinIO. Администратор отправляет боту фотографию с названием
в подписи. Товар появляется в веб-каталоге и Telegram Mini App.
Покупатель может открыть карточку, собрать корзину и оформить заказ без оплаты.

## Локальный запуск

Нужен Docker с Compose.

```sh
cp .env.example .env
docker compose build
docker compose up -d --scale api=2 --scale bot=2 --scale web=2
docker compose run --rm --no-deps api python -m app.seed
```

Открыть http://localhost:8095. Команда `app.seed` добавляет два демонстрационных
товара и безопасен для повторного запуска. Без BOT_TOKEN каталог работает
самостоятельно; Telegram подключается отдельно.

MinIO собирается из закреплённой версии upstream-исходников, поскольку
официальные готовые образы недоступны. Первая сборка загружает Go-модули;
кэш сохраняется для следующих сборок. Go используется только при сборке MinIO.

`docker compose down` останавливает сервисы и сохраняет данные. Тома PostgreSQL и MinIO
удаляются только при явном `docker compose down -v`.

## Telegram Mini App

Заполнить `.env`:

- `BOT_TOKEN` — токен от BotFather;
- `ADMIN_IDS` — числовые ID администраторов через запятую;
- `PUBLIC_URL` — публичный HTTPS-адрес gateway без пути;
- `COOKIE_SECURE=true` — для HTTPS;
- `WEBHOOK_SECRET` — случайная строка, например из `openssl rand -hex 32`.

Для временного доступа без сервера можно использовать
`cloudflared tunnel --url http://127.0.0.1:8095`. Сгенерированный адрес нужно
записать в PUBLIC_URL. После смены адреса повторить настройку webhook:

```sh
docker compose up -d --scale api=2 --scale bot=2 --scale web=2
docker compose run --rm --no-deps bot python -m bot.setup
```

В боте: `/start` открывает каталог, `/create` предлагает прислать **одно фото
с названием в подписи**. Команда создания доступна только администраторам.
Альбомы, видео, GIF и файлы не поддерживаются: бот сообщает, что товар не создан.
Максимум фото — 10 МБ, название — 200 символов.
После включения Secure cookie использовать публичный HTTPS-адрес и в браузере.

## Проверки

```sh
docker compose build tests
docker compose run --rm --no-deps tests
docker compose run --rm --no-deps tests ruff check --no-cache .
docker compose run --rm --no-deps tests ruff format --no-cache --check .
docker compose build web
```

Тесты используют реальные PostgreSQL и MinIO из Compose, отдельную базу
`catalog_test` и отдельный бакет `products-test`. Для создания тестовой базы
пользователю PostgreSQL нужно право CREATE DATABASE. Тесты не обращаются
к Telegram API: сетевой вызов диспетчера заменён в тесте webhook.

Сборка Next.js включает проверку TypeScript. Версии runtime-зависимостей закреплены
в `backend/requirements.lock`, фронтенда — в `frontend/package-lock.json`.
Тестовые зависимости устанавливаются только в Docker target `test`.

## Устройство проекта

```text
backend/
  app/
    api.py           HTTP-маршруты и cookie-сессия
    schemas.py       контракты API
    catalog.py       сценарии каталога и границы транзакций
    repository.py    SQL-запросы
    sessions.py      гостевые сессии
    storage.py       MinIO и проверка фотографий
    main.py          сборка FastAPI и обработка ошибок
  bot/
    handlers.py      обработка сообщений aiogram
    updates.py       защита от повторной доставки
    main.py          webhook и жизненный цикл бота
  migrations/        последовательные SQL-миграции
  tests/             интеграционные проверки
frontend/
  app/               страницы Next.js App Router
  components/        каталог, карточка и корзина
  lib/               типизированный API-клиент и общие функции
```

Корзины, сессии и обработанные Telegram update хранятся в PostgreSQL, фото —
в MinIO. Прикладные сервисы запускаются в нескольких репликах без sticky
sessions. Изменение корзины и checkout сериализуются блокировкой сессии;
повторный request_id возвращает существующий заказ. Название и цена товара
фиксируются в заказе. В локальном Compose PostgreSQL и MinIO одиночные;
для отказоустойчивого окружения нужны отдельные кластеры хранения.

Секреты хранятся в локальном `.env`, который исключён из Git. Значения из
`.env.example` предназначены для локального запуска. Перед внешним
развёртыванием заменить пароли и настроить HTTPS.

При разработке использовался AI.
