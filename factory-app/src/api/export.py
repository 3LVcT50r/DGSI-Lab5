import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import EventRead
from src.models.event import Event
from src.services.simulation import (
    export_state,
    import_state,
    export_inventory,
    export_events,
    import_inventory,
    import_events,
)

router = APIRouter()


@router.get("/events", response_model=List[EventRead])
def get_events(db: Session = Depends(get_db_session)):
    """List all events."""
    return db.query(Event).order_by(Event.id.desc()).limit(100).all()


@router.get("/state/export")
def get_export_state(db: Session = Depends(get_db_session)):
    """Export current simulation state as JSON."""
    return export_state(db)


@router.get("/state/export/inventory")
def get_export_inventory(db: Session = Depends(get_db_session)):
    """Export current inventory state as JSON."""
    return export_inventory(db)


@router.get("/state/export/events")
def get_export_events(db: Session = Depends(get_db_session)):
    """Export event history as JSON."""
    return export_events(db)


@router.post("/state/import/inventory")
def post_import_inventory(file: UploadFile = File(...),
                          db: Session = Depends(get_db_session)):
    """Import inventory state from uploaded JSON."""
    try:
        payload = file.file.read().decode("utf-8")
        import_inventory(db, json.loads(payload))
        return {"status": "inventory imported"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/state/import/events")
def post_import_events(file: UploadFile = File(...),
                       db: Session = Depends(get_db_session)):
    """Import event history from uploaded JSON."""
    try:
        payload = file.file.read().decode("utf-8")
        import_events(db, json.loads(payload))
        return {"status": "events imported"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
