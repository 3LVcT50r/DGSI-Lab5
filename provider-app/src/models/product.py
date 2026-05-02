from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.models.base import Base


class Product(Base):
    """A sellable product in the provider catalog."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    lead_time_days = Column(Integer, nullable=False, default=1)

    pricing_tiers = relationship(
        "PricingTier",
        back_populates="product",
        order_by="PricingTier.min_quantity",
    )
    stock = relationship("Stock", back_populates="product", uselist=False)
    orders = relationship("Order", back_populates="product")
    orders = relationship("Order", back_populates="product")
