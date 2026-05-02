from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import ManufacturingOrderRead
from src.models.order import ManufacturingOrder
from src.services.simulation import release_order

router = APIRouter()


@router.get("/orders", response_model=List[ManufacturingOrderRead])
def get_orders(db: Session = Depends(get_db_session)):
    """List all manufacturing orders."""
    mos = db.query(ManufacturingOrder).all()
    return mos


@router.get("/orders/{order_id}", response_model=ManufacturingOrderRead)
def get_order(order_id: int, db: Session = Depends(get_db_session)):
    """Get details of a specific manufacturing order."""
    mo = db.query(ManufacturingOrder).filter(
        ManufacturingOrder.id == order_id).first()
    if not mo:
        raise HTTPException(status_code=404, detail="Order not found")
    return mo


@router.post("/orders/{order_id}/release",
             response_model=ManufacturingOrderRead)
def post_release_order(order_id: int, db: Session = Depends(get_db_session)):
    """Release a pending manufacturing order to production."""
    try:
        return release_order(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/orders/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db_session)):
    """Cancel a pending manufacturing order."""
    mo = db.query(ManufacturingOrder).filter(
        ManufacturingOrder.id == order_id).first()
    if not mo:
        raise HTTPException(status_code=404, detail="Order not found")
    if mo.status != "pending":
        raise HTTPException(status_code=400,
                            detail="Can only cancel pending orders")
    db.delete(mo)
    db.commit()
    return {"status": "cancelled"}
