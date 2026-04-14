import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Any, Dict
from src.database import get_db_session
from src.services.simulation import (
    advance_day,
    get_simulation_status,
    reset_simulation,
    release_order,
    create_purchase_order,
    export_state,
    import_state,
)

api_router = APIRouter()


@api_router.get("/simulate/status", response_model=Dict[str, Any])
def read_simulation_status(db: Session = Depends(get_db_session)):
    """Get the current simulation status for dashboard display."""
    return get_simulation_status(db)


@api_router.post("/simulate/advance")
def post_advance_day(db: Session = Depends(get_db_session)):
    """Advance the simulated calendar by one day."""
    return advance_day(db)


@api_router.post("/simulate/reset")
def post_reset_simulation(db: Session = Depends(get_db_session)):
    """Reset the simulation state to the initial configuration."""
    reset_simulation(db)
    return {"status": "reset"}


@api_router.post("/orders/{order_id}/release")
def post_release_order(order_id: int, db: Session = Depends(get_db_session)):
    """Release a pending manufacturing order to production."""
    try:
        return release_order(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@api_router.post("/purchase-orders")
def post_purchase_order(payload: Dict[str, Any], db: Session = Depends(get_db_session)):
    """Create a new purchase order."""
    return create_purchase_order(
        db,
        supplier_id=payload.get("supplier_id"),
        product_id=payload.get("product_id"),
        quantity=payload.get("quantity"),
        expected_delivery=payload.get("expected_delivery"),
    )


@api_router.get("/state/export")
def get_export_state(db: Session = Depends(get_db_session)):
    """Export current simulation state as JSON."""
    return export_state(db)


@api_router.post("/state/import")
def post_import_state(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    """Import simulation state from uploaded JSON."""
    try:
        payload = file.file.read().decode("utf-8")
        import_state(db, __import__("json").loads(payload))
        return {"status": "imported"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
