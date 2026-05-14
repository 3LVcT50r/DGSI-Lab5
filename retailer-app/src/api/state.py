from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.services.retailer import export_state, import_state

router = APIRouter()


@router.get("/state/export")
def get_state_export(db: Session = Depends(get_db_session)) -> Dict[str, Any]:
    """Export the full retailer simulation state."""
    return export_state(db)


@router.post("/state/import")
def post_state_import(state_data: Dict[str, Any], db: Session = Depends(get_db_session)):
    """Import the retailer simulation state from JSON."""
    try:
        import_state(db, state_data)
        return {"status": "imported"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
