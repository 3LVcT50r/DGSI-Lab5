import enum
from sqlalchemy import Column, Integer, Float, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base


class PurchaseOrderStatus(enum.Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CLOSED = "closed"


class PurchaseOrder(Base):
    """A purchase order placed with the manufacturer."""

    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    issue_day = Column(Integer, nullable=False)
    expected_delivery_day = Column(Integer, nullable=False)
    status = Column(Enum(PurchaseOrderStatus), nullable=False, default=PurchaseOrderStatus.PENDING)
    manufacturer_order_id = Column(Integer, nullable=True)

    product = relationship("Product", back_populates="purchase_orders")
