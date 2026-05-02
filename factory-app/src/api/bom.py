from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import BOMRead
from src.models.bom import BOM

router = APIRouter()


@router.get("/bom", response_model=List[BOMRead])
def get_boms(db: Session = Depends(get_db_session)):
    """List all BOM definitions."""
    return db.query(BOM).all()


@router.get("/bom/product/{product_id}", response_model=List[BOMRead])
def get_bom_for_product(product_id: int,
                        db: Session = Depends(get_db_session)):
    """Get BOM for specific product."""
    boms = db.query(BOM).filter(BOM.finished_product_id == product_id).all()
    return boms
