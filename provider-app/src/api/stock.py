from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.request import Restock
from src.schemas.response import StockRead
from src.services.provider import get_stock, restock

router = APIRouter()


@router.get("/stock", response_model=List[StockRead])
def get_stock_endpoint(db: Session = Depends(get_db_session)):
    """Get current stock levels."""
    return get_stock(db)


@router.post("/stock/restock")
def restock_endpoint(payload: Restock, db: Session = Depends(get_db_session)):
    """Add inventory to a product (provider self-restock from upstream supply)."""
    try:
        restock(db, payload.product_id, payload.quantity)
        return {"status": "ok", "product_id": payload.product_id, "added": payload.quantity}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))