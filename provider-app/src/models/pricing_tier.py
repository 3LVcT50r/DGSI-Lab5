from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base


class PricingTier(Base):
    """Pricing tiers for products based on quantity."""
    __tablename__ = "pricing_tiers"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    min_quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    product = relationship("Product", back_populates="pricing_tiers")