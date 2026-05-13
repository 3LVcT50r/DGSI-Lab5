from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.models.event import Event
from src.schemas.response import EventRead

router = APIRouter()


@router.get("/events")
def get_events(db: Session = Depends(get_db_session)):
    """Get all events."""
    events = db.query(Event).all()
    return [EventRead.from_orm(event) for event in events]