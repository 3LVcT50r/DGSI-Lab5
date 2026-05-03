from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import EventRead
from src.models import Event

router = APIRouter()


@router.get("/events", response_model=List[EventRead])
def get_events(db: Session = Depends(get_db_session)):
    """List all events."""
    return db.query(Event).order_by(Event.id.desc()).limit(100).all()