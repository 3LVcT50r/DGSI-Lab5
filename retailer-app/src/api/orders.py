from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.request import CustomerOrderCreate
from src.schemas.response import CustomerOrderRead
from src.services.retailer import (
    get_customer_orders,
    get_customer_order,
    create_customer_order,
    fulfill_order,
    backorder_order,
)

router = APIRouter()


@router.get("/orders", response_model=List[CustomerOrderRead])
def get_orders_endpoint(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db_session),
):
    """List all customer orders, optionally filtered by status."""
    return get_customer_orders(db, status)


@router.get("/orders/{order_id}", response_model=CustomerOrderRead)
def get_order_endpoint(order_id: int, db: Session = Depends(get_db_session)):
    """Get a specific customer order."""
    order = get_customer_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/orders", response_model=CustomerOrderRead)
def post_order(order_data: CustomerOrderCreate, db: Session = Depends(get_db_session)):
    """Create a new customer order."""
    try:
        return create_customer_order(db, order_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/orders/{order_id}/fulfill", response_model=CustomerOrderRead)
def post_fulfill_order(order_id: int, db: Session = Depends(get_db_session)):
    """Fulfill a customer order from stock."""
    try:
        return fulfill_order(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/orders/{order_id}/backorder", response_model=CustomerOrderRead)
def post_backorder_order(order_id: int, db: Session = Depends(get_db_session)):
    """Mark a customer order as backordered."""
    try:
        return backorder_order(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
