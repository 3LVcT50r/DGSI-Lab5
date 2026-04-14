"""SQLAlchemy ORM models for the 3D Printer Factory Simulation."""

import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    JSON,
    ForeignKey,
    CheckConstraint,
    Enum as SAEnum,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ProductType(str, enum.Enum):
    """Whether a product is a raw material or a finished good."""
    RAW = "raw"
    FINISHED = "finished"


class OrderStatus(str, enum.Enum):
    """Lifecycle states for a manufacturing order."""
    PENDING = "pending"
    WAITING_FOR_MATERIALS = "waiting_for_materials"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PurchaseOrderStatus(str, enum.Enum):
    """Lifecycle states for a purchase order."""
    OPEN = "open"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class EventType(str, enum.Enum):
    """Categories for simulation events."""
    ORDER_CREATED = "order_created"
    ORDER_RELEASED = "order_released"
    ORDER_STARTED = "order_started"
    ORDER_COMPLETED = "order_completed"
    PO_CREATED = "po_created"
    PO_RECEIVED = "po_received"
    MATERIALS_CONSUMED = "materials_consumed"
    STOCKOUT = "stockout"


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------

class Product(Base):
    """A raw material or finished good tracked by the factory."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(SAEnum(ProductType), nullable=False)

    __table_args__ = (
        CheckConstraint("type IN ('RAW', 'FINISHED')", name="ck_product_type"),
    )

    inventory = relationship("Inventory", back_populates="product", uselist=False)
    bom_items = relationship(
        "BOM",
        back_populates="finished_product",
        foreign_keys="BOM.finished_product_id",
    )
    supplier_items = relationship("Supplier", back_populates="product")


class BOM(Base):
    """Bill of Materials: maps a finished product to its required raw materials."""
    __tablename__ = "bom"

    id = Column(Integer, primary_key=True, index=True)
    finished_product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_bom_quantity_positive"),
    )

    finished_product = relationship(
        "Product",
        foreign_keys=[finished_product_id],
        back_populates="bom_items",
    )
    material = relationship("Product", foreign_keys=[material_id])


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


class Inventory(Base):
    """Current stock level for a product (raw material or finished good)."""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    quantity = Column(Float, nullable=False, default=0)
    reserved = Column(Float, nullable=False, default=0)

    product = relationship("Product", back_populates="inventory")


class ManufacturingOrder(Base):
    """A customer demand order for a quantity of finished goods."""
    __tablename__ = "manufacturing_orders"

    id = Column(Integer, primary_key=True, index=True)
    created_date = Column(Integer, nullable=False)          # simulation day
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(
        SAEnum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
    )
    start_date = Column(Integer, nullable=True)             # simulation day
    completed_date = Column(Integer, nullable=True)         # simulation day

    product = relationship("Product")


class PurchaseOrder(Base):
    """A request to a supplier for raw materials."""
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    issue_date = Column(Integer, nullable=False)            # simulation day
    expected_delivery = Column(Integer, nullable=False)     # simulation day
    status = Column(
        SAEnum(PurchaseOrderStatus),
        default=PurchaseOrderStatus.OPEN,
        nullable=False,
    )

    supplier = relationship("Supplier")
    product = relationship("Product")


class Event(Base):
    """An immutable record of a simulation event."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(SAEnum(EventType), nullable=False)
    sim_date = Column(Integer, nullable=False)              # simulation day
    details = Column(JSON, nullable=False)


class SimulationState(Base):
    """Singleton tracking global simulation state."""
    __tablename__ = "simulation_state"

    id = Column(Integer, primary_key=True, index=True)
    current_day = Column(Integer, nullable=False, default=0)

