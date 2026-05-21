from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.services.retailer import get_catalog

router = APIRouter()


@router.get("/catalog")
def get_catalog_endpoint(db: Session = Depends(get_db_session)):
    """Get the product catalog with retail prices."""
    return get_catalog(db)

@router.put("/catalog/{model}/price")
def set_price_endpoint(model: str, price: float, db: Session = Depends(get_db_session)):
    """Set retail price for a product."""
    from src.services.retailer import set_price
    return set_price(db, model, price)