"""BOM model: maps finished products to raw materials."""

from sqlalchemy import (
    Column, Integer, Float,
    ForeignKey, CheckConstraint,
)
from sqlalchemy.orm import relationship
from src.models.base import Base


class BOM(Base):
    """Bill of Materials entry."""
    __tablename__ = "bom"

    id = Column(Integer, primary_key=True, index=True)
    finished_product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )
    material_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )
    quantity = Column(Float, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_bom_quantity_positive",
        ),
    )

    finished_product = relationship(
        "Product",
        foreign_keys=[finished_product_id],
        back_populates="bom_items",
    )
    material = relationship(
        "Product",
        foreign_keys=[material_id],
    )
