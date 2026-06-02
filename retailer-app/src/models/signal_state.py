"""Today's market signal received from the turn engine."""

from sqlalchemy import Column, Float, Integer, String

from src.models.base import Base


class SignalState(Base):
    """Singleton row storing the currently active market signal.

    `price_sensitivity` is a string hint (e.g. "high") that the engine can
    pass through from a scenario event so the retailer agent can choose to
    be more cautious about raising prices.
    """

    __tablename__ = "signal_state"

    id = Column(Integer, primary_key=True, index=True)
    sim_day = Column(Integer, nullable=False, default=0)
    demand_modifier = Column(Float, nullable=False, default=1.0)
    supply_modifier = Column(Float, nullable=False, default=1.0)
    lead_time_modifier = Column(Float, nullable=False, default=1.0)
    price_sensitivity = Column(String, nullable=True)
