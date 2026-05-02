from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from src.models.base import Base


class Event(Base):
    """Audit trail for all state changes."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    sim_day = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())