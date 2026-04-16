from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class PricingTierRead(BaseModel):
    min_quantity: int
    unit_price: float


class ProductCatalogRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    lead_time_days: int
    pricing: List[PricingTierRead]
    model_config = ConfigDict(from_attributes=True)


class StockRead(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    buyer: str
    product: str
    quantity: int


class OrderRead(BaseModel):
    id: int
    buyer: str
    product: str
    quantity: int
    unit_price: float
    total_price: float
    placed_day: int
    expected_delivery_day: int
    shipped_day: Optional[int] = None
    delivered_day: Optional[int] = None
    status: str
    model_config = ConfigDict(from_attributes=True)


class DayStatus(BaseModel):
    current_day: int


class ExportState(BaseModel):
    products: List[Dict[str, Any]]
    pricing_tiers: List[Dict[str, Any]]
    stock: List[Dict[str, Any]]
    orders: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    sim_state: Dict[str, Any]
