from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import InventoryRead
from src.models.inventory import Inventory
from src.services.inventory import get_inventory_levels

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
