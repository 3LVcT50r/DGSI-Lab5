from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.request import PriceSet
from src.services.retailer import set_price

router = APIRouter()


@router.post("/prices")
def post_set_price(price_data: PriceSet, db: Session = Depends(get_db_session)):
    """Set the retail price for a model."""
    try:
        return set_price(db, price_data.model, price_data.price)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
