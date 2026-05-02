from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from src.database import get_db_session
from src.schemas.response import PurchaseOrderRead, SupplierRead
from src.schemas.request import PurchaseOrderCreate
from src.models.purchase_order import PurchaseOrder
from src.models.supplier import Supplier
from src.services.simulation import create_purchase_order
from src.services.provider import get_provider_service
from src.config import Settings

def get_settings() -> Settings:
    return Settings()

router = APIRouter()


@router.get("/purchase-orders", response_model=List[PurchaseOrderRead])
def get_purchase_orders(db: Session = Depends(get_db_session)):
    """List all purchase orders."""
    pos = db.query(PurchaseOrder).all()
    return pos


@router.post("/purchase-orders", response_model=PurchaseOrderRead)
async def post_purchase_order(
        po_data: PurchaseOrderCreate, db: Session = Depends(get_db_session),
        settings: Settings = Depends(get_settings)):
    """Create a new purchase order."""
    try:
        return await create_purchase_order(
            db,
            settings,
            supplier_id=po_data.supplier_id,
            product_id=po_data.product_id,
            quantity=po_data.quantity,
            expected_delivery=0,  # Not used anymore
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/purchase-orders/{po_id}/cancel")
def cancel_purchase_order(po_id: int, db: Session = Depends(get_db_session)):
    """Cancel open PO."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    if po.status != "open":
        raise HTTPException(status_code=400,
                            detail="Only open POs can be cancelled")
    po.status = "cancelled"
    db.commit()
    return {"status": "cancelled"}


@router.get("/catalog")
async def get_catalog(settings: Settings = Depends(get_settings)):
    """Get the product catalog from provider."""
    provider_service = get_provider_service(settings)
    try:
        catalog = await provider_service.get_catalog()
        return catalog
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=500, detail=f"Provider error: {exc}")


@router.get("/suppliers", response_model=List[SupplierRead])
def get_suppliers(db: Session = Depends(get_db_session)):
    """List all suppliers (legacy, now returns empty)."""
    # Since we now use provider, this might be deprecated
    return []


@router.get("/suppliers/{supplier_id}/catalog",
            response_model=List[SupplierRead])
def get_supplier_catalog(supplier_id: int,
                         db: Session = Depends(get_db_session)):
    """Get catalog for a supplier (legacy)."""
    # Deprecated
    return []
