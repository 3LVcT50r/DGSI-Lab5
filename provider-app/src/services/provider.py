"""Business logic for the provider app."""

import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.models import Product, PricingTier, Stock, Order, OrderStatus, Event, SimState
from src.schemas.request import OrderCreate
from src.schemas.response import CatalogItemRead, StockRead, OrderRead

logger = logging.getLogger(__name__)


def get_catalog(session: Session) -> List[CatalogItemRead]:
    """Get the full product catalog with pricing."""
    products = session.query(Product).all()
    catalog = []
    for product in products:
        pricing_tiers = [
            tier for tier in product.pricing_tiers
        ]
        catalog.append(CatalogItemRead(
            product=product,
            pricing_tiers=pricing_tiers
        ))
    return catalog


def get_stock(session: Session) -> List[StockRead]:
    """Get current stock levels."""
    stocks = session.query(Stock).all()
    return [StockRead.from_orm(stock) for stock in stocks]


def get_orders(session: Session, status: Optional[str] = None) -> List[OrderRead]:
    """Get orders, optionally filtered by status."""
    query = session.query(Order)
    if status:
        query = query.filter(Order.status == OrderStatus(status))
    orders = query.all()
    return [OrderRead.from_orm(order) for order in orders]


def get_order(session: Session, order_id: int) -> Optional[OrderRead]:
    """Get a specific order."""
    order = session.query(Order).filter(Order.id == order_id).first()
    if order:
        return OrderRead.from_orm(order)
    return None


def calculate_price(session: Session, product_id: int, quantity: float) -> float:
    """Calculate price based on quantity tiers."""
    tiers = session.query(PricingTier).filter(
        and_(PricingTier.product_id == product_id, PricingTier.min_quantity <= quantity)
    ).order_by(PricingTier.min_quantity.desc()).first()
    if not tiers:
        raise ValueError(f"No pricing tier found for product {product_id} and quantity {quantity}")
    return tiers.price * quantity


def place_order(session: Session, order_data: OrderCreate) -> OrderRead:
    """Place a new order."""
    
    if order_data.quantity < 0:
        raise ValueError("Quantity must be non-negative")


    # Get product for lead time
    product = session.query(Product).filter(Product.id == order_data.product_id).first()
    if not product:
        raise ValueError("Product not found")

    # Get current day
    sim_state = session.query(SimState).first()
    current_day = sim_state.current_day if sim_state else 0

    # Calculate price
    total_price = calculate_price(session, order_data.product_id, order_data.quantity)

    # Create order
    order = Order(
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        status=OrderStatus.PENDING,
        expected_delivery_day=current_day + product.lead_time_days,
        total_price=total_price
    )
    session.add(order)
    session.flush()

    # Reduce stock
    

    # Log event
    event = Event(
        sim_day=current_day,
        event_type="order_placed",
        entity_type="order",
        entity_id=order.id,
        detail=f"Order placed for {order_data.quantity} units of product {order_data.product_id}, product is pending stock review"
    )
    session.add(event)

    session.commit()
    return OrderRead.from_orm(order)


def advance_day(session: Session) -> int:
    """Advance the simulation by one day."""
    sim_state = session.query(SimState).first()
    if not sim_state:
        sim_state = SimState(current_day=0)
        session.add(sim_state)
    current_day = sim_state.current_day + 1
    sim_state.current_day = current_day
    
    

    # Move confirmed orders to in progress
    orders_to_deliver = session.query(Order).filter(
        and_(Order.status == OrderStatus.DELIVERED, Order.expected_delivery_day <= current_day)
    ).all()

    for order in orders_to_deliver:
        session.delete(order)
        event = Event(
            sim_day=current_day,
            event_type="order_finished",
            entity_type="order",
            entity_id=order.id,
            detail=f"Order {order.id} finished, has been delivered"
        )
        session.add(event)
    
    confirmed_orders = session.query(Order).filter(Order.status == OrderStatus.CONFIRMED).all()
    for order in confirmed_orders:
        # Check stock
        stock = session.query(Stock).filter(Stock.product_id == order.product_id).first()
        if stock and stock.quantity >= order.quantity:
            stock.quantity -= order.quantity
            order.status = OrderStatus.IN_PROGRESS
            event = Event(
                sim_day=current_day,
                event_type="order_started",
                entity_type="order",
                entity_id=order.id,
                detail=f"Order {order.id} started processing"
            )
            session.add(event)
        else:
            event = Event(
                sim_day=current_day,
                event_type="order_pending_stock",
                entity_type="order",
                entity_id=order.id,
                detail=f"Order {order.id} pending stock, cannot start"
            )
            session.add(event)

    # Process orders
    orders_to_ship = session.query(Order).filter(
        and_(Order.status == OrderStatus.IN_PROGRESS, Order.expected_delivery_day <= current_day)
    ).all()

    for order in orders_to_ship:
        order.status = OrderStatus.SHIPPED
        event = Event(
            sim_day=current_day,
            event_type="order_shipped",
            entity_type="order",
            entity_id=order.id,
            detail=f"Order {order.id} ready and shipped"
        )
        session.add(event)
        
    orders_to_deliver = session.query(Order).filter(
        and_(Order.status == OrderStatus.SHIPPED, Order.expected_delivery_day <= current_day)
    ).all()

    for order in orders_to_deliver:
        order.status = OrderStatus.DELIVERED
        event = Event(
            sim_day=current_day,
            event_type="order_delivered",
            entity_type="order",
            entity_id=order.id,
            detail=f"Order {order.id} delivered"
        )
        session.add(event)

    # Log day advance
    event = Event(
        sim_day=current_day,
        event_type="day_advanced",
        detail=f"Day advanced to {current_day}"
    )
    session.add(event)

    session.commit()
    return current_day


def get_current_day(session: Session) -> int:
    """Get the current simulated day."""
    sim_state = session.query(SimState).first()
    return sim_state.current_day if sim_state else 0


def set_price(session: Session, product_id: int, min_quantity: int, price: float):
    """Set or update pricing tier."""
    current_day = get_current_day(session)
    tier = session.query(PricingTier).filter(
        and_(PricingTier.product_id == product_id, PricingTier.min_quantity == min_quantity)
    ).first()
    if tier:
        tier.price = price
    else:
        tier = PricingTier(
            product_id=product_id,
            min_quantity=min_quantity,
            price=price
        )
        session.add(tier)
    
    event = Event(
        sim_day=current_day,
        event_type="price_changed",
        entity_type="pricing_tier",
        entity_id=tier.id,
        detail=f"Price set for product {product_id}, qty {min_quantity}+ to ${price:.2f}"
    )
    session.add(event)
    session.commit()


def restock(session: Session, product_id: int, quantity: float):
    """Add stock to a product."""
    current_day = get_current_day(session)
    stock = session.query(Stock).filter(Stock.product_id == product_id).first()
    if stock:
        stock.quantity += quantity
    else:
        stock = Stock(product_id=product_id, quantity=quantity)
        session.add(stock)
    
    event = Event(
        sim_day=current_day,
        event_type="stock_updated",
        entity_type="stock",
        entity_id=stock.id,
        detail=f"Stock updated for product {product_id}, added {quantity} units"
    )
    session.add(event)
    session.commit()


def export_state(session: Session) -> str:
    """Export the current state to JSON."""
    products = session.query(Product).all()
    pricing_tiers = session.query(PricingTier).all()
    stocks = session.query(Stock).all()
    orders = session.query(Order).all()
    events = session.query(Event).all()
    sim_state = session.query(SimState).first()

    data = {
        "products": [p.__dict__ for p in products],
        "pricing_tiers": [pt.__dict__ for pt in pricing_tiers],
        "stocks": [s.__dict__ for s in stocks],
        "orders": [o.__dict__ for o in orders],
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

    return json.dumps(data, indent=2, default=str)


def import_state(session: Session, json_str: str):
    """Import state from JSON."""
    data = json.loads(json_str)

    # Clear existing data
    session.query(Event).delete()
    session.query(Order).delete()
    session.query(Stock).delete()
    session.query(PricingTier).delete()
    session.query(Product).delete()
    session.query(SimState).delete()
    session.commit()

    # Insert new data
    for p in data.get("products", []):
        p.pop('id', None)  # Remove id to let DB assign
        session.add(Product(**p))

    session.commit()  # Commit to get IDs

    for pt in data.get("pricing_tiers", []):
        pt.pop('id', None)
        session.add(PricingTier(**pt))

    for s in data.get("stocks", []):
        s.pop('id', None)
        session.add(Stock(**s))

    for o in data.get("orders", []):
        o.pop('id', None)
        session.add(Order(**o))

    for e in data.get("events", []):
        e.pop('id', None)
        session.add(Event(**e))

    if data.get("sim_state"):
        ss = data["sim_state"]
        ss.pop('id', None)
        session.add(SimState(**ss))

    session.commit()