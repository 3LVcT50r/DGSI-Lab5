from pydantic import BaseModel
from typing import Optional


class OrderCreate(BaseModel):
    customer: str
    model: str
    quantity: int


class PurchaseOrderCreate(BaseModel):
    model: str
    quantity: int


class PriceSet(BaseModel):
    model: str
    price: float