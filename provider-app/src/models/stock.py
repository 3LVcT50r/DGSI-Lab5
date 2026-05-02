from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base


class Stock(Base):
    """Stock levels for products."""
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=0)

    product = relationship("Product", back_populates="stock")