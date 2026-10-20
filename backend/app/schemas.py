from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    id: int
    name: str
    price_kopecks: int


class ProductList(BaseModel):
    items: list[Product]


class CartItem(Product):
    quantity: int


class Cart(BaseModel):
    items: list[CartItem]


class Quantity(BaseModel):
    quantity: int = Field(ge=0, le=99)


class OrderRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    request_id: UUID
    name: str = Field(min_length=1, max_length=200)
    contact: str = Field(min_length=1, max_length=300)


class Order(BaseModel):
    id: UUID
    total_kopecks: int
