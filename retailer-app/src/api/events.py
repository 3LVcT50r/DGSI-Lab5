from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.models import Event
from src.schemas.response import EventRead

router = APIRouter()


@router.get("/events", response_model=List[EventRead])
def get_events_endpoint(db: Session = Depends(get_db_session)):
    """List recent event history."""
    return db.query(Event).order_by(Event.id.desc()).limit(100).all()
