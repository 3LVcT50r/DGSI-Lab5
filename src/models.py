import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    JSON,
    Enum as SAEnum,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ProductType(str, enum.Enum):
    RAW = "raw"
    FINISHED = "finished"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(SAEnum(ProductType), nullable=False)

    inventory = relationship("Inventory", back_populates="product", uselist=False)
    bom_items = relationship("BOM", back_populates="finished_product", foreign_keys="BOM.finished_product_id")
    supplier_items = relationship("Supplier", back_populates="product")


class BOM(Base):
    __tablename__ = "bom"

    id = Column(Integer, primary_key=True, index=True)
    finished_product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    finished_product = relationship("Product", foreign_keys=[finished_product_id], back_populates="bom_items")
    material = relationship("Product", foreign_keys=[material_id])


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    unit_cost = Column(Float, nullable=False)
    lead_time_days = Column(Integer, nullable=False)

    product = relationship("Product", back_populates="supplier_items")


class Inventory(Base):
    __tablename__ = "inventory"

    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="inventory")


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ManufacturingOrder(Base):
    __tablename__ = "manufacturing_orders"

    id = Column(Integer, primary_key=True, index=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(SAEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)

    product = relationship("Product")


class PurchaseOrderStatus(str, enum.Enum):
    OPEN = "open"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    issue_date = Column(DateTime, default=datetime.utcnow)
    expected_delivery = Column(DateTime, nullable=False)
    status = Column(SAEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.OPEN, nullable=False)

    supplier = relationship("Supplier")
    product = relationship("Product")


class EventType(str, enum.Enum):
    ORDER_CREATED = "order_created"
    ORDER_RELEASED = "order_released"
    ORDER_STARTED = "order_started"
    ORDER_COMPLETED = "order_completed"
    PO_CREATED = "po_created"
    PO_RECEIVED = "po_received"
    MATERIALS_CONSUMED = "materials_consumed"
    STOCKOUT = "stockout"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(SAEnum(EventType), nullable=False)
    sim_date = Column(DateTime, default=datetime.utcnow)
    detail = Column(JSON, nullable=False)


class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    day = Column(Integer, nullable=False, unique=True)
    total_inventory = Column(Integer, default=0)
    pending_orders = Column(Integer, default=0)
    completed_orders = Column(Integer, default=0)
    open_purchase_orders = Column(Integer, default=0)
    production_output = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
