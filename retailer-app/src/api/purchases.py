from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.request import PurchaseOrderCreate
from src.services.retailer import get_purchase_orders, place_purchase_order

router = APIRouter()


@router.get("/purchases")
def get_purchase_orders_endpoint(db: Session = Depends(get_db_session)):
    """List purchase orders placed with manufacturer."""
    return get_purchase_orders(db)


@router.post("/purchases")
def post_purchase_order(order_data: PurchaseOrderCreate, db: Session = Depends(get_db_session)):
    """Place a purchase order with the manufacturer."""
    try:
        return place_purchase_order(db, order_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))