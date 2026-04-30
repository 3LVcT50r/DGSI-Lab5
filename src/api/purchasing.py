from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.schemas.response import PurchaseOrderRead, SupplierRead
from src.models.purchase_order import PurchaseOrder
from src.models.supplier import Supplier
from src.services.simulation import create_purchase_order

router = APIRouter()


@router.get("/purchase-orders", response_model=List[PurchaseOrderRead])
def get_purchase_orders(db: Session = Depends(get_db_session)):
    """List all purchase orders."""
    pos = db.query(PurchaseOrder).all()
    return pos


@router.post("/purchase-orders", response_model=PurchaseOrderRead)
def post_purchase_order(
        payload: Dict[str, Any], db: Session = Depends(get_db_session)):
    """Create a new purchase order."""
    try:
        return create_purchase_order(
            db,
            supplier_id=payload.get("supplier_id"),
            product_id=payload.get("product_id"),
            quantity=payload.get("quantity"),
            expected_delivery=payload.get("expected_delivery", 0),
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


@router.get("/suppliers", response_model=List[SupplierRead])
def get_suppliers(db: Session = Depends(get_db_session)):
    """List all suppliers."""
    return db.query(Supplier).all()


@router.get("/suppliers/{supplier_id}/catalog",
            response_model=List[SupplierRead])
def get_supplier_catalog(supplier_id: int,
                         db: Session = Depends(get_db_session)):
    """Get catalog for a supplier."""
    items = db.query(Supplier).filter(Supplier.id == supplier_id).all()
    return items
