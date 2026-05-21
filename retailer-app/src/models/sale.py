from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base


class Sale(Base):
    """A completed customer sale record."""

    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("customer_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    sales_price = Column(Float, nullable=False)
    margin_pct = Column(Float, nullable=False)
    completed_day = Column(Integer, nullable=False)

    order = relationship("CustomerOrder", back_populates="sale")
    product = relationship("Product", back_populates="sales")
