from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import SalesOrderRead
from src.schemas.request import SalesOrderCreate
from src.models.order import SalesOrder, SimulationState
from src.models.event import EventType
from src.services.simulation import release_sales_order
from src.services.simulation import log_event

router = APIRouter()


@router.get("/sales-orders", response_model=List[SalesOrderRead])
def get_sales_orders(db: Session = Depends(get_db_session)):
    """List all sales orders."""
    sos = db.query(SalesOrder).all()
    return sos


@router.get("/sales-orders/{order_id}", response_model=SalesOrderRead)
def get_sales_order(order_id: int, db: Session = Depends(get_db_session)):
    """Get details of a specific sales order."""
    so = db.query(SalesOrder).filter(
        SalesOrder.id == order_id).first()
    if not so:
        raise HTTPException(status_code=404, detail="Order not found")
    return so


@router.post("/orders", response_model=SalesOrderRead)
def create_order(order: SalesOrderCreate, db: Session = Depends(get_db_session)):
    """Create a new sales order from a retailer."""
    # Find product by name
    from src.models.product import Product
    product = db.query(Product).filter(Product.name == order.product_name).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{order.product_name}' not found")
    if product.type != "finished":
        raise HTTPException(status_code=400, detail="Can only order finished products")

    # Get current day
    sim_state = db.query(SimulationState).first()
    current_day = sim_state.current_day if sim_state else 0

    sales_order = SalesOrder(
        created_date=current_day,
        retailer_name=order.retailer_name,
        product_id=product.id,
        quantity=order.quantity,
    )
    db.add(sales_order)
    db.flush()
    log_event(
        db,
        EventType.SALES_ORDER_CREATED,
        current_day,
        {
            "sales_order_id": sales_order.id,
            "retailer": sales_order.retailer_name,
            "product_id": sales_order.product_id,
            "qty": sales_order.quantity,
        },
    )
    db.commit()
    db.refresh(sales_order)
    return sales_order


@router.post("/sales-orders/{order_id}/release",
             response_model=SalesOrderRead)
def post_release_sales_order(order_id: int, db: Session = Depends(get_db_session)):
    """Release a sales order to production."""
    try:
        return release_sales_order(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/sales-orders/{order_id}")
def delete_sales_order(order_id: int, db: Session = Depends(get_db_session)):
    """Cancel a pending sales order."""
    so = db.query(SalesOrder).filter(
        SalesOrder.id == order_id).first()
    if not so:
        raise HTTPException(status_code=404, detail="Order not found")
    if so.status != "received":
        raise HTTPException(status_code=400,
                            detail="Can only cancel received orders")
    db.delete(so)
    db.commit()
    return {"status": "cancelled"}