import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.models.base import Base


class OrderStatus(str, enum.Enum):
    """Lifecycle states for a customer order."""
    PENDING = "pending"
    FULFILLED = "fulfilled"
    BACKORDERED = "backordered"


class CustomerOrder(Base):
    """An order from an end customer."""
    __tablename__ = "customer_orders"

    id = Column(Integer, primary_key=True, index=True)
    customer = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status: Column[OrderStatus] = Column(
        SAEnum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
    )
    created_day = Column(Integer, nullable=False)
    fulfilled_day = Column(Integer, nullable=True)

    product = relationship("Product", back_populates="customer_orders")