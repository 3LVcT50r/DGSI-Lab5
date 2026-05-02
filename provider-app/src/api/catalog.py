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