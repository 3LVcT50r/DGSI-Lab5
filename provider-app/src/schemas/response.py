"""Response schemas (DTOs) for API serialisation."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ProductRead(BaseModel):
    """Product response."""
    id: int
    name: str
    description: Optional[str]
    lead_time_days: int
    model_config = ConfigDict(from_attributes=True)


class PricingTierRead(BaseModel):
    """Pricing tier response."""
    min_quantity: int
    price: float
    model_config = ConfigDict(from_attributes=True)


class CatalogItemRead(BaseModel):
    """Catalog item with pricing."""
    product: ProductRead
    pricing_tiers: List[PricingTierRead]
    model_config = ConfigDict(from_attributes=True)


class StockRead(BaseModel):
    """Stock response."""
    product_id: int
    quantity: float
    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    """Order response."""
    id: int
    product_id: int
    quantity: float
    status: str
    placed_at: datetime
    expected_delivery_day: int
    total_price: float
    model_config = ConfigDict(from_attributes=True)


class DayRead(BaseModel):
    """Current day response."""
    current_day: int