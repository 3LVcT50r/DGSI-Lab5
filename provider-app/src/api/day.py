from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import DayRead
from src.services.provider import advance_day, get_current_day

router = APIRouter()


@router.post("/day/advance", response_model=DayRead)
def post_advance_day(db: Session = Depends(get_db_session)):
    """Advance the simulation by one day."""
    new_day = advance_day(db)
    return DayRead(current_day=new_day)


@router.get("/day/current", response_model=DayRead)
def get_current_day_endpoint(db: Session = Depends(get_db_session)):
    """Get the current simulated day."""
    current_day = get_current_day(db)
    return DayRead(current_day=current_day)