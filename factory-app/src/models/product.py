import enum
from sqlalchemy import Column, Integer, String, CheckConstraint, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.models.base import Base


class ProductType(str, enum.Enum):
    """Whether a product is a raw material or a finished good."""
    RAW = "raw"
    FINISHED = "finished"


class Product(Base):
    """A raw material or finished good tracked by the factory."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type: Column[ProductType] = Column(SAEnum(ProductType), nullable=False)

    __table_args__ = (
        CheckConstraint("type IN ('RAW', 'FINISHED')", name="ck_product_type"),
    )

    inventory = relationship(
        "Inventory",
        back_populates="product",
        uselist=False)
    bom_items = relationship(
        "BOM",
        back_populates="finished_product",
        foreign_keys="BOM.finished_product_id",
    )
    supplier_items = relationship("Supplier", back_populates="product")
