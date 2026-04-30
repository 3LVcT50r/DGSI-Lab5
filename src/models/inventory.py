from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base


class Inventory(Base):
    """Current stock level for a product (raw material or finished good)."""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        unique=True,
        nullable=False)
    quantity = Column(Float, nullable=False, default=0)
    reserved = Column(Float, nullable=False, default=0)

    product = relationship("Product", back_populates="inventory")
