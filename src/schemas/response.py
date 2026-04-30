"""Response schemas (DTOs) for API serialisation."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from src.schemas.request import (
    ProductBase,
    SupplierBase,
    ManufacturingOrderBase,
)


class ProductRead(ProductBase):
    """Product response."""
    id: int
    model_config = ConfigDict(from_attributes=True)


class BOMRead(BaseModel):
    """BOM response."""
    id: int
    finished_product_id: int
    material_id: int
    quantity: float
    model_config = ConfigDict(from_attributes=True)


class SupplierRead(SupplierBase):
    """Supplier response."""
    id: int
    model_config = ConfigDict(from_attributes=True)


class InventoryRead(BaseModel):
    """Inventory response."""
    product_id: int
    quantity: float
    reserved: float = 0
    model_config = ConfigDict(from_attributes=True)


class ManufacturingOrderRead(ManufacturingOrderBase):
    """Manufacturing order response."""
    id: int
    created_date: int
    status: str
    start_date: Optional[int] = None
    completed_date: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderRead(BaseModel):
    """Purchase order response."""
    id: int
    supplier_id: Optional[int] = None
    provider_name: Optional[str] = None
    provider_order_id: Optional[int] = None
    product_id: int
    quantity: int
    issue_date: int
    expected_delivery: int
    status: str
    model_config = ConfigDict(from_attributes=True)


class EventRead(BaseModel):
    """Event response."""
    id: int
    sim_day: int
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    detail: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SimulationStatus(BaseModel):
    """Composite dashboard status response."""
    current_day: int
    pending_orders: List[ManufacturingOrderRead]
    inventory_levels: List[InventoryRead]
    open_purchase_orders: List[PurchaseOrderRead]
