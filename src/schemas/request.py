from pydantic import BaseModel
from enum import Enum


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
    product_id: int
    quantity: int
