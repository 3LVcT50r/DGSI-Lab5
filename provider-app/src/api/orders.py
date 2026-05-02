from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.request import OrderCreate
from src.schemas.response import OrderRead
from src.services.provider import get_orders, get_order, place_order

router = APIRouter()


@router.get("/orders", response_model=List[OrderRead])
def get_orders_endpoint(status: Optional[str] = Query(None), db: Session = Depends(get_db_session)):
    """List all orders, optionally filtered by status."""
    return get_orders(db, status)


@router.get("/orders/{order_id}", response_model=OrderRead)
def get_order_endpoint(order_id: int, db: Session = Depends(get_db_session)):
    """Get details of a specific order."""
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/orders", response_model=OrderRead)
def post_order(order_data: OrderCreate, db: Session = Depends(get_db_session)):
    """Place a new order."""
    try:
        return place_order(db, order_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))