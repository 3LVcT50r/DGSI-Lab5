"""Today's market signal received from the turn engine."""

from sqlalchemy import Column, Float, Integer

from src.models.base import Base


class SignalState(Base):
    """Singleton row storing the currently active market signal.

    The turn engine POSTs `/api/v1/signal` at the start of each simulated day
    with the modifiers active for that day. The provider reads
    `lead_time_modifier` here when computing `expected_delivery_day` so that
    a chip shortage or similar event can stretch real lead times.
    """

    __tablename__ = "signal_state"

    id = Column(Integer, primary_key=True, index=True)
    sim_day = Column(Integer, nullable=False, default=0)
    demand_modifier = Column(Float, nullable=False, default=1.0)
    supply_modifier = Column(Float, nullable=False, default=1.0)
    lead_time_modifier = Column(Float, nullable=False, default=1.0)
