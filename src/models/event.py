import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from src.models.base import Base


class EventType(str, enum.Enum):
    """Categories for simulation events."""
    # Manufacturer existing ones (mapped to new if applicable)
    ORDER_CREATED = "order_placed"
    ORDER_RELEASED = "order_released"
    ORDER_STARTED = "order_started"
    ORDER_COMPLETED = "order_completed"
    PO_CREATED = "po_created"
    PO_RECEIVED = "po_received"
    MATERIALS_CONSUMED = "materials_consumed"
    STOCKOUT = "stockout"
    
    # New global ones from requirements
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    PRICE_CHANGED = "price_changed"
    STOCK_UPDATED = "stock_updated"
    DAY_ADVANCED = "day_advanced"


class Event(Base):
    """An immutable record of a simulation event."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sim_day = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
