import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import EventRead
from src.models.event import Event
from src.services.simulation import export_state, import_state

router = APIRouter()


@router.get("/events", response_model=List[EventRead])
def get_events(db: Session = Depends(get_db_session)):
    """List all events."""
    return db.query(Event).order_by(Event.id.desc()).limit(100).all()


@router.get("/state/export")
def get_export_state(db: Session = Depends(get_db_session)):
    """Export current simulation state as JSON."""
    return export_state(db)


@router.post("/state/import")
def post_import_state(file: UploadFile = File(...),
                      db: Session = Depends(get_db_session)):
    """Import simulation state from uploaded JSON."""
    try:
        payload = file.file.read().decode("utf-8")
        import_state(db, json.loads(payload))
        return {"status": "imported"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
