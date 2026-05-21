import enum
from sqlalchemy import Column, Integer, JSON, Enum as SAEnum
from src.models.base import Base


class EventType(str, enum.Enum):
    """Categories for simulation events."""
    ORDER_CREATED = "order_created"
    ORDER_RELEASED = "order_released"
    ORDER_STARTED = "order_started"
    ORDER_COMPLETED = "order_completed"
    SALES_ORDER_CREATED = "sales_order_created"
    SALES_ORDER_RELEASED = "sales_order_released"
    SALES_ORDER_SHIPPED = "sales_order_shipped"
    SALES_ORDER_DELIVERED = "sales_order_delivered"
    PO_CREATED = "po_created"
    PO_RECEIVED = "po_received"
    MATERIALS_CONSUMED = "materials_consumed"
    STOCKOUT = "stockout"


class Event(Base):
    """An immutable record of a simulation event."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    type: Column[EventType] = Column(SAEnum(EventType), nullable=False)
    sim_date = Column(Integer, nullable=False)              # simulation day
    details = Column(JSON, nullable=False)
