from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.request import SalesOrderCreate
from src.schemas.response import SalesOrderRead
from src.models.order import SalesOrder, SalesOrderStatus
from src.services.sales import create_sales_order, get_sales_orders

router = APIRouter()


@router.post("/sales-orders", response_model=SalesOrderRead)
def post_sales_order(order_data: SalesOrderCreate, db: Session = Depends(get_db_session)):
    """Accept a sales order from a retailer."""
    try:
        return create_sales_order(db, order_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/sales-orders", response_model=List[SalesOrderRead])
def get_sales_orders_endpoint(db: Session = Depends(get_db_session)):
    """List all sales orders received from retailers."""
    return get_sales_orders(db)


@router.get("/sales-orders/{order_id}", response_model=SalesOrderRead)
def get_sales_order(order_id: int, db: Session = Depends(get_db_session)):
    """Get details of a specific sales order."""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return order


@router.post("/sales-orders/{order_id}/release")
def post_release_sales_order(order_id: int, db: Session = Depends(get_db_session)):
    """Release a sales order to production."""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    if order.status != SalesOrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order is not pending")
    
    order.status = SalesOrderStatus.RELEASED
    db.commit()
    return {"status": "released"}