from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base


class Supplier(Base):
    """A vendor that sells raw materials at a given price and lead time."""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    unit_cost = Column(Float, nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    min_order_qty = Column(Integer, nullable=False, default=1)

    product = relationship("Product", back_populates="supplier_items")
