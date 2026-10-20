from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from app import catalog, schemas, sessions, storage
from app.settings import settings

router = APIRouter(prefix="/api")


def customer_session(request: Request, response: Response) -> UUID:
    if request.method not in {"GET", "HEAD"} and request.headers.get(
        "origin"
    ) != settings.public_url.rstrip("/"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Недопустимый источник запроса")
    cookie = request.cookies.get(sessions.COOKIE_NAME)
    session_id = sessions.get_or_create(cookie)
    if str(session_id) != cookie:
        response.set_cookie(
            sessions.COOKIE_NAME,
            str(session_id),
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            max_age=sessions.SESSION_MAX_AGE,
            path="/",
        )
    return session_id


Session = Annotated[UUID, Depends(customer_session)]


@router.get("/products", response_model=schemas.ProductList)
def products(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return {"items": catalog.products(limit, offset)}


@router.get("/products/{product_id}", response_model=schemas.Product)
def product(product_id: int):
    return catalog.product(product_id)


@router.get("/products/{product_id}/image")
async def image(product_id: int):
    row = await run_in_threadpool(catalog.product, product_id)
    stream = await run_in_threadpool(storage.open_photo, row["image_key"])
    return StreamingResponse(
        storage.photo_chunks(stream),
        media_type="image/jpeg",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.get("/cart", response_model=schemas.Cart)
def cart(session_id: Session):
    return {"items": catalog.cart(session_id)}


@router.put("/cart/{product_id}", response_model=schemas.Cart)
def set_quantity(product_id: int, body: schemas.Quantity, session_id: Session):
    return {"items": catalog.set_quantity(session_id, product_id, body.quantity)}


@router.post(
    "/orders", status_code=status.HTTP_201_CREATED, response_model=schemas.Order
)
def checkout(body: schemas.OrderRequest, session_id: Session):
    return catalog.checkout(session_id, body.request_id, body.name, body.contact)
