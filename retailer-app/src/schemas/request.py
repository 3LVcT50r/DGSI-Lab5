from typing import Optional
from pydantic import BaseModel, Field


class CustomerOrderCreate(BaseModel):
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: int
    customer_name: str

    def __init__(self, **data):
        super().__init__(**data)
        if self.product_id is None and self.product_name is None:
            raise ValueError("Either product_id or product_name must be provided")
        if self.product_id is not None and self.product_name is not None:
            raise ValueError("Provide either product_id or product_name, not both")


class PurchaseCreate(BaseModel):
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: int

    def __init__(self, **data):
        super().__init__(**data)
        if self.product_id is None and self.product_name is None:
            raise ValueError("Either product_id or product_name must be provided")
        if self.product_id is not None and self.product_name is not None:
            raise ValueError("Provide either product_id or product_name, not both")


class PriceUpdate(BaseModel):
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    price: float

    def __init__(self, **data):
        super().__init__(**data)
        if self.product_id is None and self.product_name is None:
            raise ValueError("Either product_id or product_name must be provided")
        if self.product_id is not None and self.product_name is not None:
            raise ValueError("Provide either product_id or product_name, not both")


class ImportState(BaseModel):
    state: dict = Field(...)
