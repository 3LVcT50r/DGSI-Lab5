from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import CatalogItemRead
from src.services.provider import get_catalog

router = APIRouter()


@router.get("/catalog", response_model=List[CatalogItemRead])
def get_catalog_endpoint(db: Session = Depends(get_db_session)):
    """Get the full product catalog with pricing."""
    return get_catalog(db)

@router.put("/catalog/{product_id}/price")
def set_price_endpoint(product_id: int, min_quantity: int, price: float, db: Session = Depends(get_db_session)):
    """Set or update pricing tier."""
    from src.services.provider import set_price
    set_price(db, product_id, min_quantity, price)
    return {"status": "success"}