from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.config import Settings
from src.schemas.request import PurchaseCreate
from src.schemas.response import PurchaseOrderRead
from src.services.retailer import get_purchase_orders, get_purchase_order, create_purchase_order

router = APIRouter()


def get_settings() -> Settings:
    return Settings()


@router.get("/purchases", response_model=List[PurchaseOrderRead])
def get_purchases_endpoint(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db_session),
):
    """List all purchase orders."""
    return get_purchase_orders(db, status)


@router.get("/purchases/{order_id}", response_model=PurchaseOrderRead)
def get_purchase_endpoint(order_id: int, db: Session = Depends(get_db_session)):
    order = get_purchase_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return order


@router.post("/purchases", response_model=PurchaseOrderRead)
def post_purchase(
    purchase_data: PurchaseCreate,
    db: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    """Create a purchase order with the manufacturer."""
    try:
        return create_purchase_order(db, settings, purchase_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
