from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProductRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    manufacturer_price: float
    retail_price: float
    model_config = ConfigDict(from_attributes=True)


class StockRead(BaseModel):
    product_id: int
    quantity_available: float
    quantity_on_hold: float
    model_config = ConfigDict(from_attributes=True)


class CustomerOrderRead(BaseModel):
    id: int
    customer_name: str
    product_id: int
    quantity: int
    status: str
    created_day: int
    fulfilled_day: Optional[int]
    total_price: float
    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    issue_day: int
    expected_delivery_day: int
    status: str
    manufacturer_order_id: Optional[int]
    model_config = ConfigDict(from_attributes=True)


class DayRead(BaseModel):
    current_day: int
    model_config = ConfigDict(from_attributes=True)


class EventRead(BaseModel):
    id: int
    sim_day: int
    event_type: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    detail: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
