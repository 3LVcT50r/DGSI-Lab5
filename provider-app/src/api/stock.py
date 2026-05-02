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