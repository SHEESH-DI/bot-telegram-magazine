import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from psycopg import OperationalError

from app.api import router
from app.db import connect
from app.errors import (
    CatalogError,
    Conflict,
    InvalidInput,
    NotFound,
    StorageUnavailable,
)

log = logging.getLogger(__name__)
ERROR_STATUS = {
    NotFound: status.HTTP_404_NOT_FOUND,
    Conflict: status.HTTP_409_CONFLICT,
    InvalidInput: status.HTTP_422_UNPROCESSABLE_CONTENT,
    StorageUnavailable: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def create_app() -> FastAPI:
    app = FastAPI(title="Каталог")
    app.include_router(router)

    @app.exception_handler(CatalogError)
    async def catalog_error(request: Request, exc: CatalogError):
        if isinstance(exc, StorageUnavailable):
            log.error("Ошибка хранилища", exc_info=exc)
        return JSONResponse(
            {"detail": str(exc)},
            status_code=ERROR_STATUS.get(
                type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
        )

    @app.exception_handler(OperationalError)
    async def database_unavailable(request: Request, exc: OperationalError):
        log.error("База недоступна", exc_info=exc)
        return JSONResponse(
            {"detail": "Сервис временно недоступен"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @app.middleware("http")
    async def no_cache(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/health")
    def health():
        with connect() as connection:
            connection.execute("SELECT 1")
        return {"status": "ok"}

    return app


app = create_app()
