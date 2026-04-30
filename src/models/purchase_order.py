from sqlalchemy import Column, Integer, ForeignKey, Enum as SAEnum, String
from sqlalchemy.orm import relationship
from src.models.base import Base
from src.models.common import OrderState


class PurchaseOrder(Base):
    """A request to a supplier for raw materials."""
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    provider_name = Column(String, nullable=True)
    provider_order_id = Column(Integer, nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    issue_date = Column(Integer, nullable=False)            # simulation day
    expected_delivery = Column(Integer, nullable=False)     # simulation day
    status: Column[OrderState] = Column(
        SAEnum(OrderState),
        default=OrderState.PENDING,
        nullable=False,
    )

    supplier = relationship("Supplier")
    product = relationship("Product")
