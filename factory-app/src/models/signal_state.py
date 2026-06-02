"""Today's market signal received from the turn engine."""

from sqlalchemy import Column, Float, Integer

from src.models.base import Base


class SignalState(Base):
    """Singleton row storing the currently active market signal.

    Stored mostly for observability and so agent prompts can see consistent
    modifiers across days. The factory does not currently change its own
    behaviour based on these values, but they show up in metrics snapshots
    so the offline analysis can correlate decisions with the active event.
    """

    __tablename__ = "signal_state"

    id = Column(Integer, primary_key=True, index=True)
    sim_day = Column(Integer, nullable=False, default=0)
    demand_modifier = Column(Float, nullable=False, default=1.0)
    supply_modifier = Column(Float, nullable=False, default=1.0)
    lead_time_modifier = Column(Float, nullable=False, default=1.0)
