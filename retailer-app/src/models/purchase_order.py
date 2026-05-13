import enum
from sqlalchemy import Column, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.models.base import Base


class PurchaseOrderStatus(str, enum.Enum):
    """Lifecycle states for a purchase order."""
    OPEN = "open"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseOrder(Base):
    """An order placed with the manufacturer."""
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status: Column[PurchaseOrderStatus] = Column(
        SAEnum(PurchaseOrderStatus),
        default=PurchaseOrderStatus.OPEN,
        nullable=False,
    )
    issue_day = Column(Integer, nullable=False)
    expected_delivery_day = Column(Integer, nullable=False)
    manufacturer_order_id = Column(Integer, nullable=True)

    product = relationship("Product", back_populates="purchase_orders")