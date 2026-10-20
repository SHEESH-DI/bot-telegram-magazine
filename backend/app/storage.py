from collections.abc import Iterator
from functools import lru_cache
from io import BytesIO

from minio import Minio
from minio.error import S3Error
from PIL import Image, UnidentifiedImageError
from urllib3 import PoolManager
from urllib3.exceptions import HTTPError
from urllib3.response import BaseHTTPResponse
from urllib3.util import Timeout

from app.errors import InvalidInput, NotFound, StorageUnavailable
from app.settings import settings

MAX_PHOTO_BYTES = 10 * 1024 * 1024


@lru_cache(maxsize=1)
def client() -> Minio:
    return Minio(
        settings.s3_endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        secure=settings.s3_secure,
        http_client=PoolManager(timeout=Timeout(connect=5, read=20), retries=False),
    )


def save_photo(key: str, photo: bytes) -> None:
    if not photo or len(photo) > MAX_PHOTO_BYTES:
        raise InvalidInput("Фото должно быть не больше 10 МБ")
    try:
        with Image.open(BytesIO(photo)) as image:
            if image.format != "JPEG":
                raise InvalidInput("Нужна фотография JPEG")
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise InvalidInput("Не удалось прочитать фотографию") from exc
    try:
        client().put_object(
            settings.s3_bucket,
            key,
            BytesIO(photo),
            len(photo),
            content_type="image/jpeg",
        )
    except (S3Error, HTTPError, OSError) as exc:
        raise StorageUnavailable("Не удалось сохранить фотографию") from exc


def open_photo(key: str) -> BaseHTTPResponse:
    try:
        return client().get_object(settings.s3_bucket, key)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchObject"}:
            raise NotFound("Фото не найдено") from exc
        raise StorageUnavailable("Фото временно недоступно") from exc
    except (HTTPError, OSError) as exc:
        raise StorageUnavailable("Фото временно недоступно") from exc


def photo_chunks(stream: BaseHTTPResponse) -> Iterator[bytes]:
    try:
        yield from stream.stream(64 * 1024)
    finally:
        stream.close()
        stream.release_conn()
