from pydantic import BaseModel
from typing import Optional


class OrderCreate(BaseModel):
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: float
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.product_id is None and self.product_name is None:
            raise ValueError("Either product_id (int) or product_name (str) must be provided")
        if self.product_id is not None and self.product_name is not None:
            raise ValueError("Provide either product_id or product_name, not both")


class PriceSet(BaseModel):
    product_id: int
    min_quantity: int
    price: float


class Restock(BaseModel):
    product_id: int
    quantity: float