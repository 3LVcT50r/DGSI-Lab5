from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import ProductRead
from src.models.product import Product

router = APIRouter()


@router.get("/products", response_model=List[ProductRead])
def get_products(db: Session = Depends(get_db_session)):
    """List all products."""
    return db.query(Product).all()
