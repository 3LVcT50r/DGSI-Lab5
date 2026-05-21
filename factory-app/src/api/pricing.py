from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import ProductRead
from src.models.product import Product

router = APIRouter()


@router.get("/pricing", response_model=List[ProductRead])
def get_price_list(db: Session = Depends(get_db_session)):
    """Get wholesale price list for finished products."""
    products = db.query(Product).filter(Product.type == "finished").all()
    return products


@router.put("/pricing/{product_name}")
def set_price(product_name: str, price: float, db: Session = Depends(get_db_session)):
    """Set wholesale price for a product."""
    product = db.query(Product).filter(Product.name == product_name).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_name}' not found")
    if product.type != "finished":
        raise HTTPException(status_code=400, detail="Can only set price for finished products")
    product.wholesale_price = price
    db.commit()
    return {"status": "updated"}