from sqlalchemy import Column, Integer
from src.models.base import Base


class SimState(Base):
    """Current simulated day."""
    __tablename__ = "sim_state"

    id = Column(Integer, primary_key=True, index=True)
    current_day = Column(Integer, nullable=False, default=0)