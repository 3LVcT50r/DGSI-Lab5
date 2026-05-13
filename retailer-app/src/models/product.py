from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from src.models.base import Base


class Product(Base):
    """A sellable printer model."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    wholesale_price = Column(Float, nullable=False)
    retail_price = Column(Float, nullable=False)

    stock = relationship("Stock", back_populates="product", uselist=False)
    customer_orders = relationship("CustomerOrder", back_populates="product")
    purchase_orders = relationship("PurchaseOrder", back_populates="product")