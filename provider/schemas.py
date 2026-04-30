from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class PricingTierRead(BaseModel):
    min_quantity: int
    unit_price: float
    model_config = ConfigDict(from_attributes=True)

class ProductRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    lead_time_days: int
    pricing_tiers: List[PricingTierRead]
    model_config = ConfigDict(from_attributes=True)

class StockRead(BaseModel):
    product_name: str
    quantity: int
    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    product_name: str
    quantity: int
    buyer: str

class OrderRead(BaseModel):
    id: int
    buyer: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    placed_day: int
    expected_delivery_day: int
    shipped_day: Optional[int]
    delivered_day: Optional[int]
    status: str
    model_config = ConfigDict(from_attributes=True)
