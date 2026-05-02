from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base
import enum


class OrderStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


class Order(Base):
    """Purchase orders from manufacturers."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    placed_at = Column(DateTime, server_default=func.now())
    expected_delivery_day = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)

    product = relationship("Product", back_populates="orders")