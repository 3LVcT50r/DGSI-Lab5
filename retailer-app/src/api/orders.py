from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.request import OrderCreate
from src.services.retailer import (
    get_customer_orders,
    get_customer_order,
    place_customer_order,
    fulfill_customer_order,
    backorder_customer_order,
)

router = APIRouter()


@router.post("/orders")
def post_customer_order(order_data: OrderCreate, db: Session = Depends(get_db_session)):
    """Place a new customer order."""
    try:
        return place_customer_order(db, order_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/orders")
def get_customer_orders_endpoint(status: Optional[str] = Query(None), db: Session = Depends(get_db_session)):
    """List customer orders, optionally filtered by status."""
    return get_customer_orders(db, status)


@router.get("/orders/{order_id}")
def get_customer_order_endpoint(order_id: int, db: Session = Depends(get_db_session)):
    """Get details of a specific customer order."""
    order = get_customer_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/orders/{order_id}/fulfill")
def post_fulfill_order(order_id: int, db: Session = Depends(get_db_session)):
    """Fulfill a customer order from stock."""
    try:
        return fulfill_customer_order(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/orders/{order_id}/backorder")
def post_backorder_order(order_id: int, db: Session = Depends(get_db_session)):
    """Mark a customer order as backordered."""
    try:
        return backorder_customer_order(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))