"""Business logic for the retailer app."""

import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.models import Product, CustomerOrder, OrderStatus, PurchaseOrder, PurchaseOrderStatus, Stock, SimState, Event
from src.schemas.request import OrderCreate, PurchaseOrderCreate, PriceSet
from src.schemas.response import ProductRead, StockRead, CustomerOrderRead, PurchaseOrderRead, CatalogItem

logger = logging.getLogger(__name__)


def get_catalog(session: Session) -> List[CatalogItem]:
    """Get the full product catalog with retail prices."""
    products = session.query(Product).all()
    catalog = []
    for product in products:
        catalog.append(CatalogItem(
            product=ProductRead.model_validate(product),
            retail_price=product.retail_price
        ))
    return catalog


def get_stock(session: Session) -> List[StockRead]:
    """Get current stock levels."""
    stocks = session.query(Stock).all()
    return [StockRead.from_orm(stock) for stock in stocks]


def get_customer_orders(session: Session, status: Optional[str] = None) -> List[CustomerOrderRead]:
    """Get customer orders, optionally filtered by status."""
    query = session.query(CustomerOrder)
    if status:
        query = query.filter(CustomerOrder.status == OrderStatus(status))
    orders = query.all()
    return [CustomerOrderRead.from_orm(order) for order in orders]


def get_customer_order(session: Session, order_id: int) -> Optional[CustomerOrderRead]:
    """Get a specific customer order."""
    order = session.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    if order:
        return CustomerOrderRead.from_orm(order)
    return None


def place_customer_order(session: Session, order_data: OrderCreate) -> CustomerOrderRead:
    """Place a new customer order."""
    # Find product by name
    product = session.query(Product).filter(Product.name.ilike(order_data.model)).first()
    if not product:
        raise ValueError(f"Product '{order_data.model}' not found")
    
    current_day = get_current_day(session)
    
    order = CustomerOrder(
        customer=order_data.customer,
        product_id=product.id,
        quantity=order_data.quantity,
        status=OrderStatus.PENDING,
        created_day=current_day,
    )
    session.add(order)
    session.flush()
    
    # Log event
    event = Event(
        sim_day=current_day,
        event_type="customer_order_placed",
        entity_type="customer_order",
        entity_id=order.id,
        detail=f"Customer order placed for {order_data.quantity} units of {order_data.model}"
    )
    session.add(event)
    
    session.commit()
    return CustomerOrderRead.from_orm(order)


def fulfill_customer_order(session: Session, order_id: int) -> CustomerOrderRead:
    """Fulfill a customer order from stock."""
    order = session.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    if not order:
        raise ValueError("Order not found")
    
    if order.status != OrderStatus.PENDING:
        raise ValueError(f"Order is in status {order.status.value}, cannot fulfill")
    
    # Check stock
    stock = session.query(Stock).filter(Stock.product_id == order.product_id).first()
    if not stock or stock.quantity < order.quantity:
        raise ValueError("Insufficient stock to fulfill order")
    
    # Deduct stock
    stock.quantity -= order.quantity
    order.status = OrderStatus.FULFILLED
    order.fulfilled_day = get_current_day(session)
    
    # Log event
    event = Event(
        sim_day=get_current_day(session),
        event_type="customer_order_fulfilled",
        entity_type="customer_order",
        entity_id=order.id,
        detail=f"Customer order fulfilled, {order.quantity} units shipped"
    )
    session.add(event)
    
    session.commit()
    return CustomerOrderRead.from_orm(order)


def backorder_customer_order(session: Session, order_id: int) -> CustomerOrderRead:
    """Mark a customer order as backordered."""
    order = session.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    if not order:
        raise ValueError("Order not found")
    
    if order.status != OrderStatus.PENDING:
        raise ValueError(f"Order is in status {order.status.value}, cannot backorder")
    
    order.status = OrderStatus.BACKORDERED
    
    # Log event
    event = Event(
        sim_day=get_current_day(session),
        event_type="customer_order_backordered",
        entity_type="customer_order",
        entity_id=order.id,
        detail=f"Customer order backordered due to stock shortage"
    )
    session.add(event)
    
    session.commit()
    return CustomerOrderRead.from_orm(order)


def get_purchase_orders(session: Session) -> List[PurchaseOrderRead]:
    """Get all purchase orders placed with manufacturer."""
    orders = session.query(PurchaseOrder).all()
    return [PurchaseOrderRead.from_orm(order) for order in orders]


def place_purchase_order(session: Session, order_data: PurchaseOrderCreate) -> PurchaseOrderRead:
    """Place a purchase order with the manufacturer."""
    # Find product by name
    product = session.query(Product).filter(Product.name.ilike(order_data.model)).first()
    if not product:
        raise ValueError(f"Product '{order_data.model}' not found")
    
    current_day = get_current_day(session)
    
    # Call manufacturer API to place order
    import httpx
    from src.config import Settings
    settings = Settings()
    
    # Get manufacturer URL from config
    with open(settings.default_seed_path, "r") as f:
        config = json.load(f)
    manufacturer_url = config.get("manufacturer", {}).get("url", "http://localhost:8002")
    
    payload = {
        "product_id": product.id,
        "quantity": order_data.quantity
    }
    
    try:
        response = httpx.post(f"{manufacturer_url}/api/v1/orders", json=payload)
        response.raise_for_status()
        manufacturer_order = response.json()
    except Exception as exc:
        raise ValueError(f"Failed to place order with manufacturer: {exc}")
    
    # Assume 2-day lead time for manufacturer
    expected_delivery = current_day + 2
    
    po = PurchaseOrder(
        product_id=product.id,
        quantity=order_data.quantity,
        status=PurchaseOrderStatus.OPEN,
        issue_day=current_day,
        expected_delivery_day=expected_delivery,
        manufacturer_order_id=manufacturer_order["id"]
    )
    session.add(po)
    session.flush()
    
    # Log event
    event = Event(
        sim_day=current_day,
        event_type="purchase_order_placed",
        entity_type="purchase_order",
        entity_id=po.id,
        detail=f"Purchase order placed with manufacturer for {order_data.quantity} units of {order_data.model}"
    )
    session.add(event)
    
    session.commit()
    return PurchaseOrderRead.from_orm(po)


def set_price(session: Session, model: str, price: float) -> ProductRead:
    """Set retail price for a product."""
    product = session.query(Product).filter(Product.name.ilike(model)).first()
    if not product:
        raise ValueError(f"Product '{model}' not found")
    
    # Check minimum markup (15% above wholesale)
    min_price = product.wholesale_price * 1.15
    if price < min_price:
        raise ValueError(f"Price must be at least ${min_price:.2f} (15% markup on wholesale)")
    
    product.retail_price = price
    
    # Log event
    event = Event(
        sim_day=get_current_day(session),
        event_type="price_changed",
        entity_type="product",
        entity_id=product.id,
        detail=f"Retail price set to ${price:.2f} for {model}"
    )
    session.add(event)
    
    session.commit()
    return ProductRead.from_orm(product)


def advance_day(session: Session) -> int:
    """Advance the simulation by one day."""
    sim_state = session.query(SimState).first()
    if not sim_state:
        sim_state = SimState(current_day=0)
        session.add(sim_state)
    current_day = sim_state.current_day + 1
    sim_state.current_day = current_day
    
    # Process deliveries from manufacturer
    delivered_pos = session.query(PurchaseOrder).filter(
        and_(PurchaseOrder.status == PurchaseOrderStatus.OPEN,
             PurchaseOrder.expected_delivery_day <= current_day)
    ).all()
    
    for po in delivered_pos:
        # Add to stock
        stock = session.query(Stock).filter(Stock.product_id == po.product_id).first()
        if stock:
            stock.quantity += po.quantity
        else:
            stock = Stock(product_id=po.product_id, quantity=po.quantity)
            session.add(stock)
        
        po.status = PurchaseOrderStatus.RECEIVED
        
        # Log event
        event = Event(
            sim_day=current_day,
            event_type="purchase_order_received",
            entity_type="purchase_order",
            entity_id=po.id,
            detail=f"Received {po.quantity} units from manufacturer"
        )
        session.add(event)
    
    # Auto-fulfill backordered orders that now have stock
    backordered_orders = session.query(CustomerOrder).filter(
        CustomerOrder.status == OrderStatus.BACKORDERED
    ).all()
    
    for order in backordered_orders:
        stock = session.query(Stock).filter(Stock.product_id == order.product_id).first()
        if stock and stock.quantity >= order.quantity:
            stock.quantity -= order.quantity
            order.status = OrderStatus.FULFILLED
            order.fulfilled_day = current_day
            
            # Log event
            event = Event(
                sim_day=current_day,
                event_type="backorder_fulfilled",
                entity_type="customer_order",
                entity_id=order.id,
                detail=f"Backordered order auto-fulfilled with new stock"
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


def reset_simulation(session: Session) -> None:
    """Reset simulation. Wipes DB and reseeds."""
    from pathlib import Path
    from src.services.seed import seed_database_from_config
    config_path = Path(__file__).parent.parent.parent / "data" / "seed-retailer.json"
    seed_database_from_config(session, config_path)