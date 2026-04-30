from sqlalchemy import Column, Integer, String, Float, Text, DateTime, func, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from provider.database import Base
from src.models.common import OrderState

class Event(Base):
    """An immutable record of a simulation event."""
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sim_day = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())

class SimState(Base):
    """Stores the current simulation day using a KV schema."""
    __tablename__ = "sim_state"
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)

class Product(Base):
    """Product catalog."""
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    lead_time_days = Column(Integer, nullable=False)
    
    pricing_tiers = relationship("PricingTier", back_populates="product", cascade="all, delete-orphan")
    stock = relationship("Stock", back_populates="product", uselist=False, cascade="all, delete-orphan")

class PricingTier(Base):
    """Quantity-based pricing tiers."""
    __tablename__ = "pricing_tiers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    min_quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    
    product = relationship("Product", back_populates="pricing_tiers")

class Stock(Base):
    """Current inventory."""
    __tablename__ = "stock"
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=0)
    
    product = relationship("Product", back_populates="stock")

class Order(Base):
    """A customer order received by the provider."""
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    placed_day = Column(Integer, nullable=False)
    expected_delivery_day = Column(Integer, nullable=False)
    shipped_day = Column(Integer, nullable=True)
    delivered_day = Column(Integer, nullable=True)
    status: Column[OrderState] = Column(
        SAEnum(OrderState),
        default=OrderState.PENDING,
        nullable=False,
    )
    
    product = relationship("Product")
