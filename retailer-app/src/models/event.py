from sqlalchemy import Column, Integer, String, Text
from src.models.base import Base


class Event(Base):
    """Audit trail of simulation events."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    sim_day = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=False)