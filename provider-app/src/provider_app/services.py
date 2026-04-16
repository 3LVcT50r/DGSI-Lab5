import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import delete
from sqlalchemy.orm import Session

from provider_app import models
from provider_app.config import settings


def _dump_detail(detail: Any) -> str:
    return json.dumps(detail, default=str)


def get_current_day(session: Session) -> int:
    state = session.query(models.SimState).filter_by(key="current_day").first()
    if state is None:
        return 0
    return int(state.value)


def set_current_day(session: Session, day: int) -> None:
    state = session.query(models.SimState).filter_by(key="current_day").first()
    if state is None:
        state = models.SimState(key="current_day", value=str(day))
        session.add(state)
    else:
        state.value = str(day)


def load_seed(session: Session, seed_path: Optional[Path] = None) -> None:
    seed_path = seed_path or settings.seed_path
    if session.query(models.Product).first():
        return

    with open(seed_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    for product_data in data.get("products", []):
        product = models.Product(
            name=product_data["name"],
            description=product_data.get("description"),
            lead_time_days=product_data["lead_time_days"],
        )
        session.add(product)
        session.flush()

        session.add(
            models.Stock(product_id=product.id, quantity=product_data.get("initial_stock", 0))
        )

        for pricing in product_data.get("pricing", []):
            session.add(
                models.PricingTier(
                    product_id=product.id,
                    min_quantity=pricing["min_qty"],
                    unit_price=pricing["price"],
                )
            )

    set_current_day(session, 0)
    session.commit()


def get_catalog(session: Session) -> List[Dict[str, Any]]:
    products = session.query(models.Product).order_by(models.Product.id).all()
    result = []
    for product in products:
        tiers = (
            session.query(models.PricingTier)
            .filter_by(product_id=product.id)
            .order_by(models.PricingTier.min_quantity)
            .all()
        )
        result.append(
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "lead_time_days": product.lead_time_days,
                "pricing": [
                    {"min_quantity": tier.min_quantity, "unit_price": tier.unit_price}
                    for tier in tiers
                ],
            }
        )
    return result


def get_stock(session: Session) -> List[Dict[str, Any]]:
    rows = session.query(models.Stock).order_by(models.Stock.product_id).all()
    result = []
    for stock in rows:
        product = session.get(models.Product, stock.product_id)
        result.append(
            {
                "product_id": stock.product_id,
                "product_name": product.name if product else "unknown",
                "quantity": stock.quantity,
            }
        )
    return result


def get_order(session: Session, order_id: int) -> Optional[Dict[str, Any]]:
    order = session.get(models.Order, order_id)
    if order is None:
        return None
    product = session.get(models.Product, order.product_id)
    return {
        "id": order.id,
        "buyer": order.buyer,
        "product": product.name if product else "unknown",
        "quantity": order.quantity,
        "unit_price": order.unit_price,
        "total_price": order.total_price,
        "placed_day": order.placed_day,
        "expected_delivery_day": order.expected_delivery_day,
        "shipped_day": order.shipped_day,
        "delivered_day": order.delivered_day,
        "status": order.status,
    }


def get_orders(session: Session, status: Optional[str] = None) -> List[Dict[str, Any]]:
    query = session.query(models.Order).order_by(models.Order.id)
    if status:
        query = query.filter(models.Order.status == status)
    orders = query.all()
    return [get_order(session, order.id) for order in orders]


def get_product_by_name(session: Session, product_name: str) -> Optional[models.Product]:
    return session.query(models.Product).filter(models.Product.name == product_name).first()


def get_price_for_quantity(session: Session, product_id: int, quantity: int) -> float:
    tiers = (
        session.query(models.PricingTier)
        .filter(models.PricingTier.product_id == product_id)
        .order_by(models.PricingTier.min_quantity.desc())
        .all()
    )
    for tier in tiers:
        if quantity >= tier.min_quantity:
            return tier.unit_price
    raise ValueError("No pricing tier configured for this product and quantity")


def record_event(
    session: Session,
    sim_day: int,
    event_type: str,
    entity_type: str,
    entity_id: Optional[int],
    detail: Any,
) -> None:
    session.add(
        models.Event(
            sim_day=sim_day,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=_dump_detail(detail),
        )
    )


def place_order(session: Session, buyer: str, product_name: str, quantity: int) -> Dict[str, Any]:
    product = get_product_by_name(session, product_name)
    if product is None:
        raise ValueError(f"Product '{product_name}' not found")
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    current_day = get_current_day(session)
    unit_price = get_price_for_quantity(session, product.id, quantity)
    total_price = round(unit_price * quantity, 2)
    expected_delivery_day = current_day + product.lead_time_days

    order = models.Order(
        buyer=buyer,
        product_id=product.id,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
        placed_day=current_day,
        expected_delivery_day=expected_delivery_day,
        status="pending",
    )
    session.add(order)
    session.flush()

    record_event(
        session,
        sim_day=current_day,
        event_type="order_placed",
        entity_type="order",
        entity_id=order.id,
        detail={
            "buyer": buyer,
            "product": product.name,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": total_price,
            "expected_delivery_day": expected_delivery_day,
        },
    )
    session.commit()
    return get_order(session, order.id)


def advance_day(session: Session) -> Dict[str, Any]:
    current_day = get_current_day(session)
    summary = {"day": current_day, "shipped": [], "delivered": []}

    delivered_orders = (
        session.query(models.Order)
        .filter(models.Order.status == "shipped")
        .filter(models.Order.expected_delivery_day == current_day)
        .all()
    )
    for order in delivered_orders:
        order.status = "delivered"
        order.delivered_day = current_day
        summary["delivered"].append(order.id)
        record_event(
            session,
            sim_day=current_day,
            event_type="order_delivered",
            entity_type="order",
            entity_id=order.id,
            detail={"order_id": order.id},
        )

    pending_orders = (
        session.query(models.Order)
        .filter(models.Order.status == "pending")
        .order_by(models.Order.id)
        .all()
    )
    for order in pending_orders:
        stock = session.get(models.Stock, order.product_id)
        if stock and stock.quantity >= order.quantity:
            stock.quantity -= order.quantity
            order.status = "shipped"
            order.shipped_day = current_day
            summary["shipped"].append(order.id)
            record_event(
                session,
                sim_day=current_day,
                event_type="order_shipped",
                entity_type="order",
                entity_id=order.id,
                detail={"order_id": order.id, "quantity": order.quantity},
            )

    record_event(
        session,
        sim_day=current_day,
        event_type="day_advanced",
        entity_type="sim_state",
        entity_id=None,
        detail={"previous_day": current_day},
    )
    set_current_day(session, current_day + 1)
    session.commit()
    return summary


def set_price_tier(session: Session, product_name: str, tier: int, price: float) -> None:
    product = get_product_by_name(session, product_name)
    if product is None:
        raise ValueError(f"Product '{product_name}' not found")
    tier_row = (
        session.query(models.PricingTier)
        .filter_by(product_id=product.id, min_quantity=tier)
        .first()
    )
    if tier_row:
        tier_row.unit_price = price
    else:
        session.add(
            models.PricingTier(product_id=product.id, min_quantity=tier, unit_price=price)
        )
    record_event(
        session,
        sim_day=get_current_day(session),
        event_type="pricing_updated",
        entity_type="product",
        entity_id=product.id,
        detail={"min_quantity": tier, "unit_price": price},
    )
    session.commit()


def restock(session: Session, product_name: str, quantity: int) -> None:
    if quantity <= 0:
        raise ValueError("Restock quantity must be greater than zero")
    product = get_product_by_name(session, product_name)
    if product is None:
        raise ValueError(f"Product '{product_name}' not found")
    stock = session.get(models.Stock, product.id)
    if stock is None:
        stock = models.Stock(product_id=product.id, quantity=0)
        session.add(stock)
    stock.quantity += quantity
    record_event(
        session,
        sim_day=get_current_day(session),
        event_type="stock_restocked",
        entity_type="product",
        entity_id=product.id,
        detail={"quantity": quantity, "new_stock": stock.quantity},
    )
    session.commit()


def export_state(session: Session) -> Dict[str, Any]:
    products = [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "lead_time_days": product.lead_time_days,
        }
        for product in session.query(models.Product).order_by(models.Product.id).all()
    ]
    pricing_tiers = [
        {
            "id": tier.id,
            "product_id": tier.product_id,
            "min_quantity": tier.min_quantity,
            "unit_price": tier.unit_price,
        }
        for tier in session.query(models.PricingTier).order_by(models.PricingTier.id).all()
    ]
    stock = [
        {"product_id": row.product_id, "quantity": row.quantity}
        for row in session.query(models.Stock).order_by(models.Stock.product_id).all()
    ]
    orders = [
        {
            "id": order.id,
            "buyer": order.buyer,
            "product_id": order.product_id,
            "quantity": order.quantity,
            "unit_price": order.unit_price,
            "total_price": order.total_price,
            "placed_day": order.placed_day,
            "expected_delivery_day": order.expected_delivery_day,
            "shipped_day": order.shipped_day,
            "delivered_day": order.delivered_day,
            "status": order.status,
        }
        for order in session.query(models.Order).order_by(models.Order.id).all()
    ]
    events = [
        {
            "id": event.id,
            "sim_day": event.sim_day,
            "event_type": event.event_type,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "detail": json.loads(event.detail),
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }
        for event in session.query(models.Event).order_by(models.Event.id).all()
    ]
    state = {
        row.key: row.value
        for row in session.query(models.SimState).order_by(models.SimState.key).all()
    }
    return {
        "products": products,
        "pricing_tiers": pricing_tiers,
        "stock": stock,
        "orders": orders,
        "events": events,
        "sim_state": state,
    }


def import_state(session: Session, payload: Dict[str, Any]) -> None:
    session.execute(delete(models.Event))
    session.execute(delete(models.Order))
    session.execute(delete(models.PricingTier))
    session.execute(delete(models.Stock))
    session.execute(delete(models.SimState))
    session.execute(delete(models.Product))
    session.commit()

    for product_data in payload.get("products", []):
        product = models.Product(
            id=product_data.get("id"),
            name=product_data["name"],
            description=product_data.get("description"),
            lead_time_days=product_data["lead_time_days"],
        )
        session.add(product)
    session.flush()

    for stock_data in payload.get("stock", []):
        session.add(
            models.Stock(
                product_id=stock_data["product_id"],
                quantity=stock_data["quantity"],
            )
        )

    for tier_data in payload.get("pricing_tiers", []):
        session.add(
            models.PricingTier(
                id=tier_data.get("id"),
                product_id=tier_data["product_id"],
                min_quantity=tier_data["min_quantity"],
                unit_price=tier_data["unit_price"],
            )
        )

    for order_data in payload.get("orders", []):
        session.add(
            models.Order(
                id=order_data.get("id"),
                buyer=order_data["buyer"],
                product_id=order_data["product_id"],
                quantity=order_data["quantity"],
                unit_price=order_data["unit_price"],
                total_price=order_data["total_price"],
                placed_day=order_data["placed_day"],
                expected_delivery_day=order_data["expected_delivery_day"],
                shipped_day=order_data.get("shipped_day"),
                delivered_day=order_data.get("delivered_day"),
                status=order_data["status"],
            )
        )

    for event_data in payload.get("events", []):
        session.add(
            models.Event(
                id=event_data.get("id"),
                sim_day=event_data["sim_day"],
                event_type=event_data["event_type"],
                entity_type=event_data.get("entity_type"),
                entity_id=event_data.get("entity_id"),
                detail=_dump_detail(event_data.get("detail", {})),
                created_at=datetime.fromisoformat(event_data["created_at"]) if event_data.get("created_at") else None,
            )
        )

    for key, value in payload.get("sim_state", {}).items():
        session.add(models.SimState(key=key, value=value))

    session.commit()
