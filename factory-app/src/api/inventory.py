from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.request import InventoryItem, InventoryStockUpdate
from src.schemas.response import InventoryRead
from src.models.inventory import Inventory
from src.services.inventory import (
    get_inventory_levels,
    set_inventory_stock,
    initialize_inventory,
)

router = APIRouter()


@router.get("/inventory", response_model=List[InventoryRead])
def get_inventory(db: Session = Depends(get_db_session)):
    """List all inventory items."""
    return get_inventory_levels(db)


@router.get("/inventory/{product_id}", response_model=InventoryRead)
def get_inventory_item(product_id: int, db: Session = Depends(get_db_session)):
    """Get stock of a specific inventory item."""
    inv = db.query(Inventory).filter(
        Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return inv


@router.put("/inventory/{product_id}", response_model=InventoryRead)
def set_inventory_item(
    product_id: int,
    payload: InventoryStockUpdate = Body(...),
    db: Session = Depends(get_db_session),
):
    """Set inventory quantity and reserved stock for an item."""
    try:
        return set_inventory_stock(
            db,
            product_id,
            payload.quantity,
            payload.reserved,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/inventory/initialize", response_model=List[InventoryRead])
def initialize_inventory_state(
    items: List[InventoryItem],
    db: Session = Depends(get_db_session),
):
    """Initialize inventory state from JSON items."""
    try:
        return initialize_inventory(db, [item.model_dump() for item in items])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
