import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.request import ImportState
from src.services.retailer import export_state, import_state

router = APIRouter()


@router.get("/state/export")
def get_state_export(db: Session = Depends(get_db_session)):
    """Export the full retailer application state."""
    state_json = export_state(db)
    try:
        return json.loads(state_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to serialize state")


@router.post("/state/import")
def post_state_import(
    payload: ImportState,
    db: Session = Depends(get_db_session),
):
    """Import retailer application state from JSON."""
    try:
        import_state(db, payload.state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "imported"}
