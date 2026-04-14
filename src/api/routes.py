import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Any, Dict, List
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
from src.services.inventory import get_inventory_levels
from src.models import ManufacturingOrder, Supplier
from src.schemas import ManufacturingOrderRead, SupplierRead, SimulationStatus
from src.services.metrics import get_daily_metrics_history

api_router = APIRouter()


@api_router.get("/simulate/status", response_model=SimulationStatus)
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


@api_router.get("/orders", response_model=List[ManufacturingOrderRead])
def list_manufacturing_orders(db: Session = Depends(get_db_session)):
    """List all manufacturing orders."""
    orders = db.query(ManufacturingOrder).all()
    return [
        ManufacturingOrderRead(
            id=order.id,
            product_id=order.product_id,
            quantity=order.quantity,
            created_date=order.created_date,
            status=order.status.value
        )
        for order in orders
    ]


@api_router.post("/orders/{order_id}/release")
def post_release_order(order_id: int, db: Session = Depends(get_db_session)):
    """Release a pending manufacturing order to production."""
    try:
        return release_order(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@api_router.get("/suppliers", response_model=List[SupplierRead])
def list_suppliers(db: Session = Depends(get_db_session)):
    """List all suppliers."""
    suppliers = db.query(Supplier).all()
    return [
        SupplierRead(
            id=supplier.id,
            name=supplier.name,
            product_id=supplier.product_id,
            unit_cost=supplier.unit_cost,
            lead_time_days=supplier.lead_time_days
        )
        for supplier in suppliers
    ]


@api_router.get("/inventory", response_model=List[Dict[str, Any]])
def get_inventory(db: Session = Depends(get_db_session)):
    """Get current inventory levels."""
    return get_inventory_levels(db)


@api_router.get("/metrics/history", response_model=List[Dict[str, Any]])
def get_metrics_history(limit: int = 30, db: Session = Depends(get_db_session)):
    """Get historical daily metrics."""
    metrics = get_daily_metrics_history(db, limit)
    return [
        {
            "day": m.day,
            "total_inventory": m.total_inventory,
            "pending_orders": m.pending_orders,
            "completed_orders": m.completed_orders,
            "open_purchase_orders": m.open_purchase_orders,
            "production_output": m.production_output
        }
        for m in metrics
    ]


@api_router.post("/purchase-orders")
def post_purchase_order(payload: Dict[str, Any], db: Session = Depends(get_db_session)):
    """Create a new purchase order."""
    from datetime import datetime
    return create_purchase_order(
        db,
        supplier_id=payload.get("supplier_id"),
        product_id=payload.get("product_id"),
        quantity=payload.get("quantity"),
        expected_delivery=datetime.fromisoformat(payload.get("expected_delivery"))
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
