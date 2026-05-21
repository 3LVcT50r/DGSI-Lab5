from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
import json

from src.database import get_db_session
from src.models import Product, Stock, CustomerOrder, PurchaseOrder, Event, SimState

router = APIRouter()

@router.get("/export")
def export_state_endpoint(db: Session = Depends(get_db_session)):
    """Export the current state to JSON."""
    products = db.query(Product).all()
    stocks = db.query(Stock).all()
    customer_orders = db.query(CustomerOrder).all()
    purchase_orders = db.query(PurchaseOrder).all()
    events = db.query(Event).all()
    sim_state = db.query(SimState).first()

    data = {
        "products": [p.__dict__ for p in products],
        "stocks": [s.__dict__ for s in stocks],
        "customer_orders": [o.__dict__ for o in customer_orders],
        "purchase_orders": [po.__dict__ for po in purchase_orders],
        "events": [e.__dict__ for e in events],
        "sim_state": sim_state.__dict__ if sim_state else None
    }

    # Remove SQLAlchemy internal keys
    for key in data:
        if isinstance(data[key], list):
            for item in data[key]:
                item.pop('_sa_instance_state', None)
        elif data[key]:
            data[key].pop('_sa_instance_state', None)

    return data

@router.post("/import")
async def import_state_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    """Import state from JSON file."""
    content = await file.read()
    data = json.loads(content)

    # Clear existing data
    db.query(Event).delete()
    db.query(CustomerOrder).delete()
    db.query(PurchaseOrder).delete()
    db.query(Stock).delete()
    db.query(Product).delete()
    db.query(SimState).delete()
    db.commit()

    # Insert new data
    for p in data.get("products", []):
        p.pop('id', None)
        db.add(Product(**p))
    db.commit()

    for s in data.get("stocks", []):
        s.pop('id', None)
        db.add(Stock(**s))

    for o in data.get("customer_orders", []):
        o.pop('id', None)
        db.add(CustomerOrder(**o))
        
    for po in data.get("purchase_orders", []):
        po.pop('id', None)
        db.add(PurchaseOrder(**po))

    for e in data.get("events", []):
        e.pop('id', None)
        db.add(Event(**e))

    if data.get("sim_state"):
        ss = data["sim_state"]
        ss.pop('id', None)
        db.add(SimState(**ss))

    db.commit()
    return {"status": "success"}
