"""Pydantic schemas (DTOs) for request validation and response serialisation."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Enumerations (mirrored for API layer)
# ---------------------------------------------------------------------------

class ProductType(str, Enum):
    raw = "raw"
    finished = "finished"


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class ProductBase(BaseModel):
    name: str
    type: ProductType


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# BOM
# ---------------------------------------------------------------------------

class BOMItem(BaseModel):
    material_id: int
    quantity: float
    model_config = ConfigDict(from_attributes=True)


class BOMRead(BaseModel):
    id: int
    finished_product_id: int
    material_id: int
    quantity: float
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------

class SupplierBase(BaseModel):
    name: str
    product_id: int
    unit_cost: float
    lead_time_days: int
    min_order_qty: int = 1


class SupplierRead(SupplierBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

class InventoryRead(BaseModel):
    product_id: int
    quantity: float
    reserved: float = 0
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Manufacturing Order
# ---------------------------------------------------------------------------

class ManufacturingOrderBase(BaseModel):
    product_id: int
    quantity: int


class ManufacturingOrderRead(ManufacturingOrderBase):
    id: int
    created_date: int
    status: str
    start_date: Optional[int] = None
    completed_date: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Purchase Order
# ---------------------------------------------------------------------------

class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    product_id: int
    quantity: int


class PurchaseOrderRead(BaseModel):
    id: int
    supplier_id: int
    product_id: int
    quantity: int
    issue_date: int
    expected_delivery: int
    status: str
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------

class EventRead(BaseModel):
    id: int
    type: str
    sim_date: int
    details: Dict[str, Any]
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Simulation Status (composite)
# ---------------------------------------------------------------------------

class SimulationStatus(BaseModel):
    current_day: int
    pending_orders: List[ManufacturingOrderRead]
    inventory_levels: List[InventoryRead]
    open_purchase_orders: List[PurchaseOrderRead]
