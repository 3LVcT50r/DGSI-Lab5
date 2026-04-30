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
    """A request to a supplier for raw materials."""
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    issue_date = Column(Integer, nullable=False)            # simulation day
    expected_delivery = Column(Integer, nullable=False)     # simulation day
    status: Column[PurchaseOrderStatus] = Column(
        SAEnum(PurchaseOrderStatus),
        default=PurchaseOrderStatus.OPEN,
        nullable=False,
    )

    supplier = relationship("Supplier")
    product = relationship("Product")
