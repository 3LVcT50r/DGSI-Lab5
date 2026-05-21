from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import ProductRead
from src.services.retailer import get_catalog

router = APIRouter()


@router.get("/catalog", response_model=List[ProductRead])
def get_catalog_endpoint(db: Session = Depends(get_db_session)):
    """Get the retailer catalog."""
    return get_catalog(db)
