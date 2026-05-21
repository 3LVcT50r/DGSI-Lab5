import enum
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base


class CustomerOrderStatus(enum.Enum):
    CREATED = "created"
    FULFILLED = "fulfilled"
    BACKORDERED = "backordered"
    RETURNED = "returned"


class CustomerOrder(Base):
    """An end-customer order for a finished printer."""

    __tablename__ = "customer_orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(Enum(CustomerOrderStatus), nullable=False, default=CustomerOrderStatus.CREATED)
    created_day = Column(Integer, nullable=False)
    fulfilled_day = Column(Integer, nullable=True)
    total_price = Column(Float, nullable=False)

    product = relationship("Product", back_populates="customer_orders")
    sale = relationship("Sale", back_populates="order", uselist=False)
