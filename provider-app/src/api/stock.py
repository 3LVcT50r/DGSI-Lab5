from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import StockRead
from src.services.provider import get_stock

router = APIRouter()


@router.get("/stock", response_model=List[StockRead])
def get_stock_endpoint(db: Session = Depends(get_db_session)):
    """Get current stock levels."""
    return get_stock(db)

@router.post("/stock/restock")
def restock_endpoint(product_id: int, quantity: float, db: Session = Depends(get_db_session)):
    """Add stock to a product."""
    from src.services.provider import restock
    restock(db, product_id, quantity)
    return {"status": "success"}