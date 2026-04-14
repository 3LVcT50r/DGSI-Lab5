from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Any, Dict, List
from src.schemas import SimulationStatus, PurchaseOrderRead, ManufacturingOrderRead, EventRead
from src.models import ManufacturingOrder, PurchaseOrder, OrderStatus, PurchaseOrderStatus, Event, EventType
from src.services.inventory import get_inventory_levels
from src.services.initialization import load_initial_data, clear_all_data
from src.services.metrics import record_daily_metrics


# Global simulation state (in a real app, this would be in database or cache)
_simulation_day = 0


def get_current_day() -> int:
    """Get current simulation day."""
    global _simulation_day
    return _simulation_day


def set_current_day(day: int) -> None:
    """Set current simulation day."""
    global _simulation_day
    _simulation_day = day


def advance_day(session: Session) -> Dict[str, Any]:
    """Advance the simulation one day and process daily events."""
    global _simulation_day
    _simulation_day += 1

    events = []

    # 1. Generate new manufacturing orders (simplified - random demand)
    new_orders = _generate_demand(session)
    events.extend(new_orders)

    # 2. Process purchase order arrivals
    arrived_pos = _process_purchase_arrivals(session)
    events.extend(arrived_pos)

    # 3. Complete in-progress production orders
    completed_orders = _complete_production_orders(session)
    events.extend(completed_orders)

    # 4. Start new orders (up to daily capacity)
    started_orders = _start_production_orders(session)
    events.extend(started_orders)

    # Log the day advance
    _log_event(session, EventType.ORDER_CREATED, {"action": "day_advanced", "new_day": _simulation_day})

    # Record daily metrics
    _record_daily_metrics(session, _simulation_day)

    session.commit()

    return {
        "new_day": _simulation_day,
        "events_generated": len(events),
        "events": events
    }


def get_simulation_status(session: Session) -> SimulationStatus:
    """Return current summary state for the dashboard and API."""
    # Ensure initial data is loaded
    load_initial_data(session)

    pending_orders = session.query(ManufacturingOrder).filter(
        ManufacturingOrder.status == OrderStatus.PENDING
    ).all()

    open_pos = session.query(PurchaseOrder).filter(
        PurchaseOrder.status == PurchaseOrderStatus.OPEN
    ).all()

    inventory_levels = get_inventory_levels(session)

    return SimulationStatus(
        current_day=get_current_day(),
        pending_orders=[
            ManufacturingOrderRead(
                id=order.id,
                product_id=order.product_id,
                quantity=order.quantity,
                created_date=order.created_date,
                status=order.status.value
            )
            for order in pending_orders
        ],
        inventory_levels=inventory_levels,
        open_purchase_orders=[
            PurchaseOrderRead(
                id=po.id,
                supplier_id=po.supplier_id,
                product_id=po.product_id,
                quantity=po.quantity,
                issue_date=po.issue_date,
                expected_delivery=po.expected_delivery,
                status=po.status.value
            )
            for po in open_pos
        ]
    )


def reset_simulation(session: Session) -> None:
    """Reset the simulation state to initial values."""
    global _simulation_day
    _simulation_day = 0

    clear_all_data(session)
    load_initial_data(session)

    # Log reset event
    _log_event(session, EventType.ORDER_CREATED, {"action": "simulation_reset"})


def release_order(session: Session, order_id: int) -> ManufacturingOrderRead:
    """Release a pending manufacturing order into production."""
    order = session.query(ManufacturingOrder).filter(ManufacturingOrder.id == order_id).first()
    if not order:
        raise ValueError(f"Order {order_id} not found")

    if order.status != OrderStatus.PENDING:
        raise ValueError(f"Order {order_id} is not pending")

    # Check if materials are available
    from src.services.inventory import reserve_materials
    if not reserve_materials(session, order.product_id, order.quantity):
        raise ValueError(f"Insufficient materials for order {order_id}")

    # Change status to in_progress
    order.status = OrderStatus.IN_PROGRESS
    session.commit()

    # Log event
    _log_event(session, EventType.ORDER_RELEASED, {
        "order_id": order_id,
        "product_id": order.product_id,
        "quantity": order.quantity
    })

    return ManufacturingOrderRead(
        id=order.id,
        product_id=order.product_id,
        quantity=order.quantity,
        created_date=order.created_date,
        status=order.status.value
    )


def create_purchase_order(session: Session, supplier_id: int, product_id: int, quantity: int, expected_delivery: datetime) -> PurchaseOrderRead:
    """Issue a purchase order for raw materials."""
    from src.models import Supplier

    # Validate supplier exists and sells this product
    supplier = session.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.product_id == product_id
    ).first()

    if not supplier:
        raise ValueError(f"Supplier {supplier_id} does not sell product {product_id}")

    # Create purchase order
    po = PurchaseOrder(
        supplier_id=supplier_id,
        product_id=product_id,
        quantity=quantity,
        expected_delivery=expected_delivery,
        status=PurchaseOrderStatus.OPEN
    )

    session.add(po)
    session.commit()

    # Log event
    _log_event(session, EventType.PO_CREATED, {
        "po_id": po.id,
        "supplier_id": supplier_id,
        "product_id": product_id,
        "quantity": quantity
    })

    return PurchaseOrderRead(
        id=po.id,
        supplier_id=po.supplier_id,
        product_id=po.product_id,
        quantity=po.quantity,
        issue_date=po.issue_date,
        expected_delivery=po.expected_delivery,
        status=po.status.value
    )


def _generate_demand(session: Session) -> List[Dict[str, Any]]:
    """Generate random manufacturing orders (simplified)."""
    from src.models import Product
    import random

    events = []

    # Simple random demand generation
    finished_products = session.query(Product).filter(Product.type == "finished").all()

    for product in finished_products:
        # Random demand: 0-3 units per day
        demand = random.randint(0, 3)
        if demand > 0:
            order = ManufacturingOrder(
                product_id=product.id,
                quantity=demand,
                status=OrderStatus.PENDING
            )
            session.add(order)
            session.flush()

            events.append({
                "type": "order_created",
                "order_id": order.id,
                "product_id": product.id,
                "quantity": demand
            })

    return events


def _process_purchase_arrivals(session: Session) -> List[Dict[str, Any]]:
    """Process purchase orders that have arrived."""
    from src.services.inventory import update_inventory

    current_date = datetime.utcnow()
    events = []

    # Find arrived POs
    arrived_pos = session.query(PurchaseOrder).filter(
        PurchaseOrder.status == PurchaseOrderStatus.OPEN,
        PurchaseOrder.expected_delivery <= current_date
    ).all()

    for po in arrived_pos:
        po.status = PurchaseOrderStatus.RECEIVED
        update_inventory(session, po.product_id, po.quantity)

        events.append({
            "type": "po_received",
            "po_id": po.id,
            "product_id": po.product_id,
            "quantity": po.quantity
        })

    return events


def _complete_production_orders(session: Session) -> List[Dict[str, Any]]:
    """Complete manufacturing orders (simplified - complete immediately)."""
    events = []

    # For now, complete all in-progress orders (simplified model)
    in_progress_orders = session.query(ManufacturingOrder).filter(
        ManufacturingOrder.status == OrderStatus.IN_PROGRESS
    ).all()

    for order in in_progress_orders:
        order.status = OrderStatus.COMPLETED

        # Add finished product to inventory
        from src.services.inventory import update_inventory
        update_inventory(session, order.product_id, order.quantity)

        events.append({
            "type": "order_completed",
            "order_id": order.id,
            "product_id": order.product_id,
            "quantity": order.quantity
        })

    return events


def _start_production_orders(session: Session) -> List[Dict[str, Any]]:
    """Start new production orders up to daily capacity."""
    # Simplified - for now, all released orders are started immediately
    # In a more complex model, this would consider capacity constraints
    events = []
    return events


def _log_event(session: Session, event_type: EventType, details: Dict[str, Any]) -> None:
    """Log an event to the audit trail."""
    event = Event(
        type=event_type,
        sim_date=datetime.utcnow(),
        detail=details
    )
    session.add(event)


def _record_daily_metrics(session: Session, day: int) -> None:
    """Record daily metrics for the given day."""
    # Calculate metrics
    inventory_levels = get_inventory_levels(session)
    total_inventory = sum(item.quantity for item in inventory_levels)

    pending_orders_count = session.query(ManufacturingOrder).filter(
        ManufacturingOrder.status == OrderStatus.PENDING
    ).count()

    completed_orders_count = session.query(ManufacturingOrder).filter(
        ManufacturingOrder.status == OrderStatus.COMPLETED
    ).count()

    open_pos_count = session.query(PurchaseOrder).filter(
        PurchaseOrder.status == PurchaseOrderStatus.OPEN
    ).count()

    # For now, production output is the number of completed orders
    # In a more sophisticated system, this would track actual units produced
    production_output = completed_orders_count

    # Record metrics
    record_daily_metrics(
        session=session,
        day=day,
        total_inventory=total_inventory,
        pending_orders=pending_orders_count,
        completed_orders=completed_orders_count,
        open_purchase_orders=open_pos_count,
        production_output=production_output
    )


def export_state(session: Session) -> Dict[str, Any]:
    """Export full simulation state as JSON-compatible data."""
    raise NotImplementedError("export_state is not implemented yet")


def import_state(session: Session, state: Dict[str, Any]) -> None:
    """Import simulation state from JSON data."""
    raise NotImplementedError("import_state is not implemented yet")
