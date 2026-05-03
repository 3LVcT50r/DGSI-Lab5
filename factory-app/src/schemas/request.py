from pydantic import BaseModel
from enum import Enum
from typing import Optional


class ProductType(str, Enum):
    raw = "raw"
    finished = "finished"


class ProductBase(BaseModel):
    name: str
    type: ProductType


class ProductCreate(ProductBase):
    pass


class BOMItem(BaseModel):
    material_id: int
    quantity: float


class SupplierBase(BaseModel):
    name: str
    product_id: int
    unit_cost: float
    lead_time_days: int
    min_order_qty: int = 1


class ManufacturingOrderBase(BaseModel):
    product_id: int
    quantity: int


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: int
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.product_id is None and self.product_name is None:
            raise ValueError("Either product_id (int) or product_name (str) must be provided")
        if self.product_id is not None and self.product_name is not None:
            raise ValueError("Provide either product_id or product_name, not both")


class InventoryItem(BaseModel):
    product_id: int
    quantity: float
    reserved: float = 0.0


class InventoryStockUpdate(BaseModel):
    quantity: float
    reserved: float = 0.0
