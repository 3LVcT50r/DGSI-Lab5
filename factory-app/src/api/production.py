from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import ManufacturingOrderRead
from src.models.order import ManufacturingOrder

router = APIRouter()


@router.get("/production/orders", response_model=List[ManufacturingOrderRead])
def get_production_orders(db: Session = Depends(get_db_session)):
    """List all manufacturing orders."""
    mos = db.query(ManufacturingOrder).all()
    return mos


@router.get("/production/orders/{order_id}", response_model=ManufacturingOrderRead)
def get_production_order(order_id: int, db: Session = Depends(get_db_session)):
    """Get details of a specific manufacturing order."""
    mo = db.query(ManufacturingOrder).filter(
        ManufacturingOrder.id == order_id).first()
    if not mo:
        raise HTTPException(status_code=404, detail="Order not found")
    return mo