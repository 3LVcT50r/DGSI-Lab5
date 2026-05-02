from pydantic import BaseModel


class OrderCreate(BaseModel):
    product_id: int
    quantity: float


class PriceSet(BaseModel):
    product_id: int
    min_quantity: int
    price: float


class Restock(BaseModel):
    product_id: int
    quantity: float