from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel


class ProductType(str, Enum):
    raw = "raw"
    finished = "finished"


class ProductBase(BaseModel):
    name: str
    type: ProductType


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int

    class Config:
        orm_mode = True


class BOMItem(BaseModel):
    material_id: int
    quantity: int


class SupplierBase(BaseModel):
    name: str
    product_id: int
    unit_cost: float
    lead_time_days: int


class SupplierRead(SupplierBase):
    id: int

    class Config:
        orm_mode = True


class InventoryRead(BaseModel):
    product_id: int
    quantity: int

    class Config:
        orm_mode = True


class ManufacturingOrderBase(BaseModel):
    product_id: int
    quantity: int


class ManufacturingOrderRead(ManufacturingOrderBase):
    id: int
    created_date: datetime
    status: str

    class Config:
        orm_mode = True


class PurchaseOrderBase(BaseModel):
    supplier_id: int
    product_id: int
    quantity: int
    expected_delivery: datetime


class PurchaseOrderRead(PurchaseOrderBase):
    id: int
    issue_date: datetime
    status: str

    class Config:
        orm_mode = True


class EventRead(BaseModel):
    id: int
    type: str
    sim_date: datetime
    detail: Dict[str, object]

    class Config:
        orm_mode = True


class SimulationStatus(BaseModel):
    current_day: int
    pending_orders: List[ManufacturingOrderRead]
    inventory_levels: List[InventoryRead]
    open_purchase_orders: List[PurchaseOrderRead]
