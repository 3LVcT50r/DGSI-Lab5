import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.models.base import Base


class OrderStatus(str, enum.Enum):
    """Lifecycle states for a manufacturing order."""
    PENDING = "pending"
    WAITING_FOR_MATERIALS = "waiting_for_materials"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SalesOrderStatus(str, enum.Enum):
    """Lifecycle states for a sales order (from retailers)."""
    PENDING = "pending"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELIVERED = "delivered"


class ManufacturingOrder(Base):
    """A customer demand order for a quantity of finished goods."""
    __tablename__ = "manufacturing_orders"

    id = Column(Integer, primary_key=True, index=True)
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
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=True)

    product = relationship("Product")
    sales_order = relationship("SalesOrder", back_populates="manufacturing_orders")


class SalesOrder(Base):
    """An order received from a retailer."""
    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, index=True)
    retailer = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status: Column[SalesOrderStatus] = Column(
        SAEnum(SalesOrderStatus),
        default=SalesOrderStatus.PENDING,
        nullable=False,
    )
    received_date = Column(Integer, nullable=False)         # simulation day
    released_date = Column(Integer, nullable=True)
    start_date = Column(Integer, nullable=True)            # simulation day
    completed_date = Column(Integer, nullable=True)         # simulation day
    delivered_date = Column(Integer, nullable=True)         # simulation day

    product = relationship("Product")
    manufacturing_orders = relationship("ManufacturingOrder", back_populates="sales_order")


class SimulationState(Base):
    """Singleton tracking global simulation state."""
    __tablename__ = "simulation_state"

    id = Column(Integer, primary_key=True, index=True)
    current_day = Column(Integer, nullable=False, default=0)
