import enum
from sqlalchemy import Column, Integer, ForeignKey, Enum as SAEnum, String
from sqlalchemy.orm import relationship
from src.models.base import Base


class OrderStatus(str, enum.Enum):
    """Lifecycle states for a manufacturing order."""
    PENDING = "pending"
    WAITING_FOR_MATERIALS = "waiting_for_materials"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SalesOrderStatus(str, enum.Enum):
    """Lifecycle states for a sales order."""
    RECEIVED = "received"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


class ManufacturingOrder(Base):
    """A production order for finished goods."""
    __tablename__ = "manufacturing_orders"

    id = Column(Integer, primary_key=True, index=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=True)
    created_date = Column(Integer, nullable=False)          # simulation day
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status: Column[OrderStatus] = Column(
        SAEnum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
    )
    start_date = Column(Integer, nullable=True)             # simulation day
    completed_date = Column(Integer, nullable=True)         # simulation day

    product = relationship("Product")
    sales_order = relationship("SalesOrder")


class SalesOrder(Base):
    """A sales order received from a retailer."""
    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, index=True)
    created_date = Column(Integer, nullable=False)          # simulation day
    retailer_name = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status: Column[SalesOrderStatus] = Column(
        SAEnum(SalesOrderStatus),
        default=SalesOrderStatus.RECEIVED,
        nullable=False,
    )
    released_date = Column(Integer, nullable=True)          # simulation day
    start_date = Column(Integer, nullable=True)             # simulation day
    completed_date = Column(Integer, nullable=True)         # simulation day
    shipped_date = Column(Integer, nullable=True)           # simulation day
    delivered_date = Column(Integer, nullable=True)         # simulation day

    product = relationship("Product")


class SimulationState(Base):
    """Singleton tracking global simulation state."""
    __tablename__ = "simulation_state"

    id = Column(Integer, primary_key=True, index=True)
    current_day = Column(Integer, nullable=False, default=0)
