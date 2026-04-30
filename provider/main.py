import json
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from src.models.common import OrderState

from provider.database import engine, Base, SessionLocal
from provider.models import Product, PricingTier, Stock, Order, SimState, Event
from provider.schemas import ProductRead, StockRead, OrderCreate, OrderRead

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Provider API",
    description="REST API for the parts Provider service.",
    version="0.1.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_day(db: Session) -> int:
    state = db.query(SimState).filter(SimState.key == "current_day").first()
    if state:
        return int(state.value)
    return 0

def log_event(db: Session, sim_day: int, event_type: str, detail: dict, entity_type: str = None, entity_id: int = None):
    evt = Event(
        sim_day=sim_day,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=json.dumps(detail)
    )
    db.add(evt)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/catalog", response_model=List[ProductRead])
def get_catalog(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

@app.get("/api/stock", response_model=List[StockRead])
def get_stock(db: Session = Depends(get_db)):
    stocks = db.query(Stock).all()
    result = []
    for s in stocks:
        result.append(StockRead(product_name=s.product.name, quantity=s.quantity))
    return result

@app.post("/api/orders", response_model=OrderRead)
def place_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.name == order_data.product_name).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    if order_data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    # Find applicable price tier
    tiers = sorted(product.pricing_tiers, key=lambda t: t.min_quantity, reverse=True)
    unit_price = None
    for t in tiers:
        if order_data.quantity >= t.min_quantity:
            unit_price = t.unit_price
            break
            
    if unit_price is None:
        raise HTTPException(status_code=400, detail="Quantity below minimum order quantity")

    current_day = get_current_day(db)
    # The Ironclad Rule
    expected_delivery = current_day + max(1, product.lead_time_days)
    
    order = Order(
        buyer=order_data.buyer,
        product_id=product.id,
        quantity=order_data.quantity,
        unit_price=unit_price,
        total_price=unit_price * order_data.quantity,
        placed_day=current_day,
        expected_delivery_day=expected_delivery,
        status=OrderState.PENDING
    )
    db.add(order)
    db.flush()
    
    log_event(db, current_day, "order_placed", {"quantity": order.quantity, "total": order.total_price}, "order", order.id)
    db.commit()
    db.refresh(order)
    
    return OrderRead(
        id=order.id,
        buyer=order.buyer,
        product_name=product.name,
        quantity=order.quantity,
        unit_price=order.unit_price,
        total_price=order.total_price,
        placed_day=order.placed_day,
        expected_delivery_day=order.expected_delivery_day,
        shipped_day=order.shipped_day,
        delivered_day=order.delivered_day,
        status=order.status.value
    )

@app.get("/api/orders", response_model=List[OrderRead])
def list_orders(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    orders = query.all()
    
    result = []
    for o in orders:
        result.append(OrderRead(
            id=o.id, buyer=o.buyer, product_name=o.product.name, quantity=o.quantity,
            unit_price=o.unit_price, total_price=o.total_price, placed_day=o.placed_day,
            expected_delivery_day=o.expected_delivery_day, shipped_day=o.shipped_day,
            delivered_day=o.delivered_day, status=o.status.value
        ))
    return result

@app.get("/api/orders/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderRead(
        id=o.id, buyer=o.buyer, product_name=o.product.name, quantity=o.quantity,
        unit_price=o.unit_price, total_price=o.total_price, placed_day=o.placed_day,
        expected_delivery_day=o.expected_delivery_day, shipped_day=o.shipped_day,
        delivered_day=o.delivered_day, status=o.status.value
    )

@app.post("/api/day/advance")
def advance_day(db: Session = Depends(get_db)):
    current_day = get_current_day(db)
    
    # 1. Orders whose expected_delivery == current_day transition shipped -> delivered
    arriving_orders = db.query(Order).filter(
        Order.status == OrderState.SHIPPED,
        Order.expected_delivery_day == current_day
    ).all()
    for order in arriving_orders:
        order.status = OrderState.DELIVERED
        order.delivered_day = current_day
        log_event(db, current_day, "order_delivered", {"order_id": order.id}, "order", order.id)
        
    # 2. Orders that were pending and have stock become shipped
    pending_orders = db.query(Order).filter(Order.status == OrderState.PENDING).order_by(Order.id).all()
    for order in pending_orders:
        stock = db.query(Stock).filter(Stock.product_id == order.product_id).first()
        if stock and stock.quantity >= order.quantity:
            # Deduct stock
            stock.quantity -= order.quantity
            # Transition to shipped
            order.status = OrderState.SHIPPED
            order.shipped_day = current_day
            log_event(db, current_day, "order_shipped", {"order_id": order.id, "qty": order.quantity}, "order", order.id)

    # 3. current_day increments
    next_day = current_day + 1
    state = db.query(SimState).filter(SimState.key == "current_day").first()
    if not state:
        state = SimState(key="current_day", value=str(next_day))
        db.add(state)
    else:
        state.value = str(next_day)
        
    log_event(db, next_day, "day_advanced", {"day": next_day})
    db.commit()
    return {"current_day": next_day}

@app.get("/api/day/current")
def get_day(db: Session = Depends(get_db)):
    return {"current_day": get_current_day(db)}
