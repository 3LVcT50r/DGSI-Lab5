import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas import (
    ManufacturingOrderRead,
    PurchaseOrderRead,
    InventoryRead,
    SupplierRead,
    BOMRead,
    EventRead,
    ProductRead,
)
from src.models import (
    ManufacturingOrder,
    PurchaseOrder,
    Inventory,
    Supplier,
    BOM,
    Event,
    Product,
)
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

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

@api_router.get("/simulate/status", response_model=Dict[str, Any])
def read_simulation_status(db: Session = Depends(get_db_session)):
    """Get the current simulation status for dashboard display."""
    status = get_simulation_status(db)
    return status.model_dump()


@api_router.post("/simulate/advance")
def post_advance_day(db: Session = Depends(get_db_session)):
    """Advance the simulated calendar by one day."""
    return advance_day(db)


@api_router.post("/simulate/reset")
def post_reset_simulation(db: Session = Depends(get_db_session)):
    """Reset the simulation state to the initial configuration."""
    reset_simulation(db)
    return {"status": "reset"}

# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@api_router.get("/orders", response_model=List[ManufacturingOrderRead])
def get_orders(db: Session = Depends(get_db_session)):
    """List all manufacturing orders."""
    mos = db.query(ManufacturingOrder).all()
    return mos

@api_router.get("/orders/{order_id}", response_model=ManufacturingOrderRead)
def get_order(order_id: int, db: Session = Depends(get_db_session)):
    """Get details of a specific manufacturing order."""
    mo = db.query(ManufacturingOrder).filter(ManufacturingOrder.id == order_id).first()
    if not mo:
        raise HTTPException(status_code=404, detail="Order not found")
    return mo

@api_router.post("/orders/{order_id}/release", response_model=ManufacturingOrderRead)
def post_release_order(order_id: int, db: Session = Depends(get_db_session)):
    """Release a pending manufacturing order to production."""
    try:
        return release_order(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@api_router.delete("/orders/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db_session)):
    """Cancel a pending manufacturing order."""
    mo = db.query(ManufacturingOrder).filter(ManufacturingOrder.id == order_id).first()
    if not mo:
        raise HTTPException(status_code=404, detail="Order not found")
    if mo.status != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending orders")
    db.delete(mo)
    db.commit()
    return {"status": "cancelled"}

# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

@api_router.get("/inventory", response_model=List[InventoryRead])
def get_inventory(db: Session = Depends(get_db_session)):
    """List all inventory items."""
    from src.services.inventory import get_inventory_levels
    return get_inventory_levels(db)

@api_router.get("/inventory/{product_id}", response_model=InventoryRead)
def get_inventory_item(product_id: int, db: Session = Depends(get_db_session)):
    """Get stock of a specific inventory item."""
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return inv

# ---------------------------------------------------------------------------
# Purchasing
# ---------------------------------------------------------------------------

@api_router.get("/purchase-orders", response_model=List[PurchaseOrderRead])
def get_purchase_orders(db: Session = Depends(get_db_session)):
    """List all purchase orders."""
    pos = db.query(PurchaseOrder).all()
    return pos

@api_router.post("/purchase-orders", response_model=PurchaseOrderRead)
def post_purchase_order(payload: Dict[str, Any], db: Session = Depends(get_db_session)):
    """Create a new purchase order."""
    try:
        return create_purchase_order(
            db,
            supplier_id=payload.get("supplier_id"),
            product_id=payload.get("product_id"),
            quantity=payload.get("quantity"),
            expected_delivery=payload.get("expected_delivery", 0),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@api_router.post("/purchase-orders/{po_id}/cancel")
def cancel_purchase_order(po_id: int, db: Session = Depends(get_db_session)):
    """Cancel open PO."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    if po.status != "open":
        raise HTTPException(status_code=400, detail="Only open POs can be cancelled")
    po.status = "cancelled"
    db.commit()
    return {"status": "cancelled"}

@api_router.get("/suppliers", response_model=List[SupplierRead])
def get_suppliers(db: Session = Depends(get_db_session)):
    """List all suppliers."""
    return db.query(Supplier).all()

@api_router.get("/suppliers/{supplier_id}/catalog", response_model=List[SupplierRead])
def get_supplier_catalog(supplier_id: int, db: Session = Depends(get_db_session)):
    """Get catalog for a supplier."""
    items = db.query(Supplier).filter(Supplier.id == supplier_id).all()
    return items

# ---------------------------------------------------------------------------
# BOM
# ---------------------------------------------------------------------------

@api_router.get("/bom", response_model=List[BOMRead])
def get_boms(db: Session = Depends(get_db_session)):
    """List all BOM definitions."""
    return db.query(BOM).all()

@api_router.get("/bom/product/{product_id}", response_model=List[BOMRead])
def get_bom_for_product(product_id: int, db: Session = Depends(get_db_session)):
    """Get BOM for specific product."""
    boms = db.query(BOM).filter(BOM.finished_product_id == product_id).all()
    return boms

# ---------------------------------------------------------------------------
# Events & Export
# ---------------------------------------------------------------------------

@api_router.get("/events", response_model=List[EventRead])
def get_events(db: Session = Depends(get_db_session)):
    """List all events."""
    return db.query(Event).order_by(Event.id.desc()).limit(100).all()

@api_router.get("/state/export")
def get_export_state(db: Session = Depends(get_db_session)):
    """Export current simulation state as JSON."""
    return export_state(db)

@api_router.post("/state/import")
def post_import_state(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    """Import simulation state from uploaded JSON."""
    try:
        payload = file.file.read().decode("utf-8")
        import_state(db, json.loads(payload))
        return {"status": "imported"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@api_router.get("/products", response_model=List[ProductRead])
def get_products(db: Session = Depends(get_db_session)):
    """List all products."""
    return db.query(Product).all()
