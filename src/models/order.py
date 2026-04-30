import enum
from sqlalchemy import Column, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.models.base import Base


class OrderStatus(str, enum.Enum):
    """Lifecycle states for a manufacturing order."""
    PENDING = "pending"
    WAITING_FOR_MATERIALS = "waiting_for_materials"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


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

    product = relationship("Product")


class SimulationState(Base):
    """Singleton tracking global simulation state."""
    __tablename__ = "simulation_state"

    id = Column(Integer, primary_key=True, index=True)
    current_day = Column(Integer, nullable=False, default=0)
