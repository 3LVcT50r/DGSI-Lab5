"""Business logic for the retailer app."""

import json
import logging
import random
from typing import List, Optional
from pathlib import Path

import httpx
from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.config import Settings
from src.models import (
    Product,
    Stock,
    CustomerOrder,
    CustomerOrderStatus,
    PurchaseOrder,
    PurchaseOrderStatus,
    Sale,
    Event,
    SimState,
)
from src.schemas.request import CustomerOrderCreate, PurchaseCreate, PriceUpdate
from src.schemas.response import (
    ProductRead,
    StockRead,
    CustomerOrderRead,
    PurchaseOrderRead,
    DayRead,
    EventRead,
)

logger = logging.getLogger(__name__)


def get_catalog(session: Session) -> List[ProductRead]:
    products = session.query(Product).all()
    return [ProductRead.from_orm(product) for product in products]


def get_stock(session: Session) -> List[StockRead]:
    stocks = session.query(Stock).all()
    return [StockRead.from_orm(stock) for stock in stocks]


def get_customer_orders(session: Session, status: Optional[str] = None) -> List[CustomerOrderRead]:
    query = session.query(CustomerOrder)
    if status:
        query = query.filter(CustomerOrder.status == CustomerOrderStatus(status))
    orders = query.order_by(CustomerOrder.id).all()
    return [CustomerOrderRead.from_orm(order) for order in orders]


def get_customer_order(session: Session, order_id: int) -> Optional[CustomerOrderRead]:
    order = session.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    return CustomerOrderRead.from_orm(order) if order else None


def get_purchase_orders(session: Session, status: Optional[str] = None) -> List[PurchaseOrderRead]:
    query = session.query(PurchaseOrder)
    if status:
        query = query.filter(PurchaseOrder.status == PurchaseOrderStatus(status))
    orders = query.order_by(PurchaseOrder.id).all()
    return [PurchaseOrderRead.from_orm(order) for order in orders]


def get_purchase_order(session: Session, order_id: int) -> Optional[PurchaseOrderRead]:
    order = session.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    return PurchaseOrderRead.from_orm(order) if order else None


def find_product(session: Session, product_id: Optional[int], product_name: Optional[str]) -> Product:
    if product_id is not None:
        product = session.query(Product).filter(Product.id == product_id).first()
    else:
        product = session.query(Product).filter(Product.name.ilike(product_name)).first()
    if not product:
        raise ValueError("Product not found")
    return product


def get_current_day(session: Session) -> int:
    sim_state = session.query(SimState).first()
    return sim_state.current_day if sim_state else 0


def create_customer_order(session: Session, order_data: CustomerOrderCreate) -> CustomerOrderRead:
    product = find_product(session, order_data.product_id, order_data.product_name)
    current_day = get_current_day(session)
    total_price = round(product.retail_price * order_data.quantity, 2)

    order = CustomerOrder(
        customer_name=order_data.customer_name,
        product_id=product.id,
        quantity=order_data.quantity,
        status=CustomerOrderStatus.CREATED,
        created_day=current_day,
        total_price=total_price,
    )
    session.add(order)
    session.flush()

    event = Event(
        sim_day=current_day,
        event_type="customer_order_created",
        entity_type="customer_order",
        entity_id=order.id,
        detail=f"Created order for {order.quantity} units of {product.name} for {order.customer_name}",
    )
    session.add(event)
    session.commit()
    return CustomerOrderRead.from_orm(order)


def fulfill_order(session: Session, order_id: int) -> CustomerOrderRead:
    order = session.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    if not order:
        raise ValueError("Order not found")
    if order.status == CustomerOrderStatus.FULFILLED:
        raise ValueError("Order is already fulfilled")
    if order.status == CustomerOrderStatus.RETURNED:
        raise ValueError("Cannot fulfill a returned order")

    stock = session.query(Stock).filter(Stock.product_id == order.product_id).first()
    if not stock or stock.quantity_available < order.quantity:
        raise ValueError("Insufficient stock to fulfill order")

    stock.quantity_available -= order.quantity
    order.status = CustomerOrderStatus.FULFILLED
    order.fulfilled_day = get_current_day(session)
    product = session.query(Product).filter(Product.id == order.product_id).first()
    margin_pct = 0.0
    if product.manufacturer_price > 0:
        margin_pct = round((product.retail_price - product.manufacturer_price) / product.manufacturer_price * 100.0, 2)

    sale = Sale(
        order_id=order.id,
        product_id=order.product_id,
        quantity=order.quantity,
        sales_price=order.total_price,
        margin_pct=margin_pct,
        completed_day=order.fulfilled_day,
    )
    session.add(sale)

    event = Event(
        sim_day=order.fulfilled_day,
        event_type="customer_order_fulfilled",
        entity_type="customer_order",
        entity_id=order.id,
        detail=f"Fulfilled order {order.id} for {order.quantity} units of {product.name}",
    )
    session.add(event)
    session.commit()
    return CustomerOrderRead.from_orm(order)


def backorder_order(session: Session, order_id: int) -> CustomerOrderRead:
    order = session.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    if not order:
        raise ValueError("Order not found")
    if order.status == CustomerOrderStatus.FULFILLED:
        raise ValueError("Order is already fulfilled")

    order.status = CustomerOrderStatus.BACKORDERED
    current_day = get_current_day(session)
    event = Event(
        sim_day=current_day,
        event_type="customer_order_backordered",
        entity_type="customer_order",
        entity_id=order.id,
        detail=f"Backordered customer order {order.id}",
    )
    session.add(event)
    session.commit()
    return CustomerOrderRead.from_orm(order)


def set_price(session: Session, price_update: PriceUpdate) -> ProductRead:
    product = find_product(session, price_update.product_id, price_update.product_name)
    minimum = round(product.manufacturer_price * 1.15, 2)
    if price_update.price < minimum:
        raise ValueError(
            f"Price must be at least {minimum:.2f} for {product.name}"
        )
    product.retail_price = price_update.price
    current_day = get_current_day(session)
    event = Event(
        sim_day=current_day,
        event_type="price_changed",
        entity_type="product",
        entity_id=product.id,
        detail=f"Retail price for {product.name} set to {product.retail_price:.2f}",
    )
    session.add(event)
    session.commit()
    return ProductRead.from_orm(product)


def create_purchase_order(session: Session, settings: Settings, purchase_data: PurchaseCreate) -> PurchaseOrderRead:
    product = find_product(session, purchase_data.product_id, purchase_data.product_name)
    current_day = get_current_day(session)

    url = settings.manufacturer_url.rstrip("/") + "/api/v1/orders"
    payload = {
        "quantity": purchase_data.quantity,
        "product_name": product.name,
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            manufacturer_order = response.json()
    except httpx.HTTPError as err:
        raise ValueError(f"Manufacturer request failed: {err}")

    expected_delivery = manufacturer_order.get("expected_delivery_day", current_day + 1)
    order = PurchaseOrder(
        product_id=product.id,
        quantity=purchase_data.quantity,
        issue_day=current_day,
        expected_delivery_day=expected_delivery,
        status=PurchaseOrderStatus.PENDING,
        manufacturer_order_id=manufacturer_order.get("id"),
    )
    session.add(order)
    session.flush()

    event = Event(
        sim_day=current_day,
        event_type="purchase_order_created",
        entity_type="purchase_order",
        entity_id=order.id,
        detail=(
            f"Created purchase order {order.id} for {order.quantity} units of {product.name}"
        ),
    )
    session.add(event)
    session.commit()
    return PurchaseOrderRead.from_orm(order)


def get_manufacturer_order_status(settings: Settings, manufacturer_order_id: int) -> Optional[str]:
    url = settings.manufacturer_url.rstrip("/") + f"/api/v1/orders/{manufacturer_order_id}"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
            return payload.get("status")
    except httpx.HTTPError:
        return None


def poll_manufacturer_shipments(session: Session, settings: Settings) -> None:
    purchase_orders = session.query(PurchaseOrder).filter(
        PurchaseOrder.status != PurchaseOrderStatus.DELIVERED
    ).all()
    for po in purchase_orders:
        if not po.manufacturer_order_id:
            continue
        status = get_manufacturer_order_status(settings, po.manufacturer_order_id)
        if status is None:
            continue

        if status == PurchaseOrderStatus.SHIPPED.value and po.status == PurchaseOrderStatus.PENDING:
            po.status = PurchaseOrderStatus.SHIPPED
            event = Event(
                sim_day=get_current_day(session),
                event_type="purchase_order_shipped",
                entity_type="purchase_order",
                entity_id=po.id,
                detail=f"Purchase order {po.id} shipped by manufacturer",
            )
            session.add(event)
        elif status == PurchaseOrderStatus.DELIVERED.value and po.status != PurchaseOrderStatus.DELIVERED:
            po.status = PurchaseOrderStatus.DELIVERED
            stock = session.query(Stock).filter(Stock.product_id == po.product_id).first()
            if stock:
                stock.quantity_available += po.quantity
            else:
                stock = Stock(product_id=po.product_id, quantity_available=po.quantity)
                session.add(stock)
            event = Event(
                sim_day=get_current_day(session),
                event_type="purchase_order_delivered",
                entity_type="purchase_order",
                entity_id=po.id,
                detail=(
                    f"Purchase order {po.id} delivered, added {po.quantity} units to stock"
                ),
            )
            session.add(event)


def auto_fulfill_backorders(session: Session) -> None:
    backorders = session.query(CustomerOrder).filter(
        CustomerOrder.status == CustomerOrderStatus.BACKORDERED
    ).order_by(CustomerOrder.created_day).all()
    for order in backorders:
        stock = session.query(Stock).filter(Stock.product_id == order.product_id).first()
        if not stock or stock.quantity_available < order.quantity:
            continue
        stock.quantity_available -= order.quantity
        order.status = CustomerOrderStatus.FULFILLED
        order.fulfilled_day = get_current_day(session)
        product = session.query(Product).filter(Product.id == order.product_id).first()
        margin_pct = 0.0
        if product.manufacturer_price > 0:
            margin_pct = round((product.retail_price - product.manufacturer_price) / product.manufacturer_price * 100.0, 2)
        sale = Sale(
            order_id=order.id,
            product_id=order.product_id,
            quantity=order.quantity,
            sales_price=order.total_price,
            margin_pct=margin_pct,
            completed_day=order.fulfilled_day,
        )
        session.add(sale)
        event = Event(
            sim_day=order.fulfilled_day,
            event_type="backorder_fulfilled",
            entity_type="customer_order",
            entity_id=order.id,
            detail=f"Backorder {order.id} fulfilled from newly received stock",
        )
        session.add(event)


def generate_customer_demand(session: Session, day: int, settings: Settings) -> None:
    """Generate daily customer orders (Gaussian distribution)."""
    seed_val = settings.default_config.get("retailer", {}).get("demand_seed")
    if seed_val is not None:
        random.seed(f"{seed_val}_{day}")

    config = settings.default_config
    products = session.query(Product).all()

    for product in products:
        products_cfg = config.get("products", {})
        prod_cfg = products_cfg.get(product.name, {})

        mean = prod_cfg.get("demand_mean", config.get("default_mean", 2))
        variance = prod_cfg.get("demand_variance", config.get("default_variance", 1.0))
        std_dev = variance ** 0.5

        demand_qty = int(round(random.gauss(mean, std_dev)))
        if demand_qty < 0:
            demand_qty = 0

        if demand_qty > 0:
            # Generate multiple customer orders or one large order
            for _ in range(demand_qty):
                customer_name = f"Customer_{product.id}_{day}_{_}"
                total_price = round(product.retail_price, 2)
                
                order = CustomerOrder(
                    customer_name=customer_name,
                    product_id=product.id,
                    quantity=1,
                    status=CustomerOrderStatus.CREATED,
                    created_day=day,
                    total_price=total_price,
                )
                session.add(order)
                session.flush()
                
                event = Event(
                    sim_day=day,
                    event_type="customer_order_created",
                    entity_type="customer_order",
                    entity_id=order.id,
                    detail=f"Generated customer order for 1 unit of {product.name}",
                )
                session.add(event)


def advance_day(session: Session, settings: Settings) -> int:
    sim_state = session.query(SimState).first()
    if not sim_state:
        sim_state = SimState(current_day=0)
        session.add(sim_state)
    current_day = sim_state.current_day + 1
    sim_state.current_day = current_day

    # Generate new customer demand
    generate_customer_demand(session, current_day, settings)

    poll_manufacturer_shipments(session, settings)
    auto_fulfill_backorders(session)

    event = Event(
        sim_day=current_day,
        event_type="day_advanced",
        entity_type="sim_state",
        detail=f"Advanced to day {current_day}",
    )
    session.add(event)
    session.commit()
    return current_day


def export_state(session: Session) -> str:
    products = session.query(Product).all()
    stocks = session.query(Stock).all()
    orders = session.query(CustomerOrder).all()
    purchase_orders = session.query(PurchaseOrder).all()
    sales = session.query(Sale).all()
    events = session.query(Event).all()
    sim_state = session.query(SimState).first()

    data = {
        "products": [p.__dict__ for p in products],
        "stocks": [s.__dict__ for s in stocks],
        "customer_orders": [o.__dict__ for o in orders],
        "purchase_orders": [po.__dict__ for po in purchase_orders],
        "sales": [s.__dict__ for s in sales],
        "events": [e.__dict__ for e in events],
        "sim_state": sim_state.__dict__ if sim_state else None,
    }
    for value in data.values():
        if isinstance(value, list):
            for item in value:
                item.pop("_sa_instance_state", None)
        elif isinstance(value, dict):
            value.pop("_sa_instance_state", None)

    return json.dumps(data, indent=2, default=str)


def import_state(session: Session, json_str: str) -> None:
    data = json.loads(json_str)
    session.query(Event).delete()
    session.query(Sale).delete()
    session.query(CustomerOrder).delete()
    session.query(PurchaseOrder).delete()
    session.query(Stock).delete()
    session.query(Product).delete()
    session.query(SimState).delete()
    session.commit()

    for item in data.get("products", []):
        item.pop("id", None)
        session.add(Product(**item))
    session.commit()

    for item in data.get("stocks", []):
        item.pop("id", None)
        session.add(Stock(**item))
    for item in data.get("customer_orders", []):
        item.pop("id", None)
        session.add(CustomerOrder(**item))
    for item in data.get("purchase_orders", []):
        item.pop("id", None)
        session.add(PurchaseOrder(**item))
    for item in data.get("sales", []):
        item.pop("id", None)
        session.add(Sale(**item))
    for item in data.get("events", []):
        item.pop("id", None)
        session.add(Event(**item))
    if data.get("sim_state"):
        sim_state_data = data["sim_state"]
        sim_state_data.pop("id", None)
        session.add(SimState(**sim_state_data))

    session.commit()
