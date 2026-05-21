from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from src.models.base import Base


class Product(Base):
    """A finished printer model sold by the retailer."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    manufacturer_price = Column(Float, nullable=False, default=0.0)
    retail_price = Column(Float, nullable=False, default=0.0)

    stock = relationship("Stock", back_populates="product", uselist=False)
    customer_orders = relationship("CustomerOrder", back_populates="product")
    purchase_orders = relationship("PurchaseOrder", back_populates="product")
    sales = relationship("Sale", back_populates="product")
