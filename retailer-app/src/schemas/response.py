from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class ProductRead(BaseModel):
    """Product response."""
    id: int
    name: str
    wholesale_price: float
    retail_price: float
    model_config = ConfigDict(from_attributes=True)


class StockRead(BaseModel):
    """Stock response."""
    product_id: int
    quantity: float
    model_config = ConfigDict(from_attributes=True)


class CustomerOrderRead(BaseModel):
    """Customer order response."""
    id: int
    customer: str
    product_id: int
    quantity: int
    status: str
    created_day: int
    fulfilled_day: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderRead(BaseModel):
    """Purchase order response."""
    id: int
    product_id: int
    quantity: int
    status: str
    issue_day: int
    expected_delivery_day: int
    manufacturer_order_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class CatalogItem(BaseModel):
    """Catalog item with pricing."""
    product: ProductRead
    retail_price: float


class DayRead(BaseModel):
    """Day response."""
    current_day: int


class EventRead(BaseModel):
    """Event response."""
    id: int
    sim_day: int
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    detail: str
    model_config = ConfigDict(from_attributes=True)