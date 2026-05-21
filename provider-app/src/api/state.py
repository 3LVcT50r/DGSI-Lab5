from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
import json

from src.database import get_db_session
from src.services.provider import export_state, import_state

router = APIRouter()

@router.get("/export")
def export_state_endpoint(db: Session = Depends(get_db_session)):
    """Export the current state to JSON."""
    json_str = export_state(db)
    return json.loads(json_str)

@router.post("/import")
async def import_state_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    """Import state from JSON file."""
    content = await file.read()
    import_state(db, content)
    return {"status": "success"}
