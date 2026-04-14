import json
import logging
import random
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session
from src.config import Settings
from src.models import (
    SimulationState,
    ManufacturingOrder,
    OrderStatus,
    PurchaseOrder,
    PurchaseOrderStatus,
    Product,
    ProductType,
    Event,
    EventType,
)
from src.schemas import (
    SimulationStatus,
    PurchaseOrderRead,
    ManufacturingOrderRead,
    InventoryRead,
)
from src.services.inventory import (
    reserve_materials,
    consume_materials,
    receive_purchase_order,
    get_inventory_levels,
)

logger = logging.getLogger(__name__)


def log_event(session: Session, event_type: EventType, sim_date: int, details: Dict[str, Any]):
    """Helper to write to the event log."""
    evt = Event(type=event_type, sim_date=sim_date, details=details)
    session.add(evt)


def get_current_day(session: Session) -> int:
    state = session.query(SimulationState).first()
    return state.current_day if state else 0


def generate_demand(session: Session, day: int, settings: Settings):
    """Generate daily manufacturing orders based on gaussian distribution config."""
    seed_val = settings.demand_seed
    if seed_val is not None:
        random.seed(f"{seed_val}_{day}")

    with open(settings.default_config_path, "r") as f:
        config = json.load(f)
    
    # Generate orders for each finished product
    finished_products = session.query(Product).filter(Product.type == ProductType.FINISHED).all()
    for prod in finished_products:
        # get model specific mean/variance or defaults
        models_cfg = config.get("models", {})
        prod_cfg = models_cfg.get(prod.name, {})
        
        mean = prod_cfg.get("demand_mean", config.get("default_mean", 5))
        variance = prod_cfg.get("demand_variance", config.get("default_variance", 2.0))
        std_dev = variance ** 0.5
        
        # Normal distribution, truncated at 0
        demand_qty = int(round(random.gauss(mean, std_dev)))
        if demand_qty < 0:
            demand_qty = 0
            
        if demand_qty > 0:
            mo = ManufacturingOrder(
                created_date=day,
                product_id=prod.id,
                quantity=demand_qty,
                status=OrderStatus.PENDING
            )
            session.add(mo)
            session.flush()
            log_event(session, EventType.ORDER_CREATED, day, {"order_id": mo.id, "product": prod.name, "qty": demand_qty})


def advance_day(session: Session) -> Dict[str, Any]:
    """Advance the simulation calendar by one day and process daily events."""
    settings = Settings()
    state = session.query(SimulationState).with_for_update().first()
    if not state:
        raise ValueError("Simulation state not initialized. Is seed process run?")
    
    # 1. Update day counter
    state.current_day += 1
    today = state.current_day
    
    with open(settings.default_config_path, "r") as f:
        config = json.load(f)
    
    capacity_per_day = config.get("capacity_per_day", settings.production_capacity_per_day)

    # 2. Process purchase arrivals (expected_delivery <= today)
    arriving_pos = session.query(PurchaseOrder).filter(
        PurchaseOrder.status == PurchaseOrderStatus.OPEN,
        PurchaseOrder.expected_delivery <= today
    ).with_for_update().all()
    
    for po in arriving_pos:
        receive_purchase_order(session, po.product_id, po.quantity)
        po.status = PurchaseOrderStatus.RECEIVED
        log_event(session, EventType.PO_RECEIVED, today, {
            "po_id": po.id, 
            "product_id": po.product_id, 
            "qty": po.quantity
        })

    # 3. Complete in-progress production
    in_progress = session.query(ManufacturingOrder).filter(
        ManufacturingOrder.status == OrderStatus.IN_PROGRESS
    ).with_for_update().all()

    # We assume an order takes X hours but max 1 day cycle, so any IN_PROGRESS from yesterday is completed today.
    # Note: PRD says "Assembly Time per model" but also "Daily capacity: Max units producible per day".
    # We will enforce the capacity bottleneck.
    completed_qty = 0
    for mo in in_progress:
        # Check if completing this order exceeds daily capacity
        # (Assuming they were started safely up to the capacity limit, but let's complete them all)
        mo.status = OrderStatus.COMPLETED
        mo.completed_date = today
        completed_qty += mo.quantity
        log_event(session, EventType.ORDER_COMPLETED, today, {"order_id": mo.id, "qty": mo.quantity})
        
        # Create stockout events if any demand isn't met? No, PRD says stockout happens when
        # materials reach zero. That's implicitly logged during reservation attempt failures later.

    # 4. Consume materials & Start new orders (up to remaining daily capacity)
    # We evaluate both totally new PENDING and those that were blocked before.
    pending = session.query(ManufacturingOrder).filter(
        ManufacturingOrder.status.in_([OrderStatus.PENDING, OrderStatus.WAITING_FOR_MATERIALS])
    ).order_by(ManufacturingOrder.created_date.asc()).all()

    started_qty_today = 0
    for mo in pending:
        if started_qty_today + mo.quantity > capacity_per_day:
            continue # Exceeds capacity, wait for tomorrow
        
        # Try to reserve materials
        success, missing_info = reserve_materials(session, mo.product_id, mo.quantity)
        if success:
            # Consume those reserved materials immediately since we are starting production
            consume_materials(session, mo.product_id, mo.quantity)
            
            mo.status = OrderStatus.IN_PROGRESS
            mo.start_date = today
            started_qty_today += mo.quantity
            log_event(session, EventType.MATERIALS_CONSUMED, today, {"order_id": mo.id, "qty": mo.quantity})
            log_event(session, EventType.ORDER_STARTED, today, {"order_id": mo.id, "qty": mo.quantity})
        else:
            # Failed to start due to material constraint
            mo.status = OrderStatus.WAITING_FOR_MATERIALS
            log_event(session, EventType.STOCKOUT, today, {
                "order_id": mo.id, 
                "reason": "Insufficient materials",
                "missing": missing_info
            })

    # 5. Generate demand for next simulation cycle
    generate_demand(session, today, settings)

    session.commit()
    return {"status": "advanced", "current_day": today}


def get_simulation_status(session: Session) -> SimulationStatus:
    """Return current summary state for the dashboard and API."""
    day = get_current_day(session)
    
    pending_mos = session.query(ManufacturingOrder).filter(
        ManufacturingOrder.status.in_([OrderStatus.PENDING, OrderStatus.WAITING_FOR_MATERIALS])
    ).all()
    
    open_pos = session.query(PurchaseOrder).filter(
        PurchaseOrder.status == PurchaseOrderStatus.OPEN
    ).all()
    
    inventory = get_inventory_levels(session)
    
    return SimulationStatus(
        current_day=day,
        pending_orders=[ManufacturingOrderRead.model_validate(mo) for mo in pending_mos],
        inventory_levels=inventory,
        open_purchase_orders=[PurchaseOrderRead.model_validate(po) for po in open_pos]
    )


def reset_simulation(session: Session) -> None:
    """Reset the simulation state to initial values. Wipes DB and reseeds."""
    from src.models import Base
    from src.database import engine
    from src.services.seed import seed_database_from_config
    
    # Drop and recreate tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Reseed
    settings = Settings()
    seed_database_from_config(session, str(settings.default_config_path))


def release_order(session: Session, order_id: int) -> ManufacturingOrderRead:
    """Release a pending manufacturing order into production. 
    It checks materials, reserves them, and changes state."""
    mo = session.query(ManufacturingOrder).filter(ManufacturingOrder.id == order_id).first()
    if not mo:
        raise ValueError("Order not found.")
    if mo.status not in [OrderStatus.PENDING, OrderStatus.WAITING_FOR_MATERIALS]:
        raise ValueError(f"Order is in status {mo.status.value}, cannot release.")
        
    day = get_current_day(session)
    success, missing_info = reserve_materials(session, mo.product_id, mo.quantity)
    if success:
        # We just reserve. The advance_day cycle will pick it up and consume.
        # But wait, PRD says user manually releases. If they manually release, should it be IN_PROGRESS?
        # A true manual release just means "approved for production".
        # Let's say user manual release means we mark it as IN_PROGRESS immediately and consume materials,
        # circumventing the auto-start for this specific UI action.
        consume_materials(session, mo.product_id, mo.quantity)
        mo.status = OrderStatus.IN_PROGRESS
        mo.start_date = day
        log_event(session, EventType.ORDER_RELEASED, day, {"order_id": mo.id})
        log_event(session, EventType.MATERIALS_CONSUMED, day, {"order_id": mo.id, "qty": mo.quantity})
        session.commit()
        return ManufacturingOrderRead.model_validate(mo)
    else:
        raise ValueError(f"Insufficient materials to release order. Missing: {', '.join(missing_info)}")


def create_purchase_order(session: Session, supplier_id: int, product_id: int, quantity: int, expected_delivery: int) -> PurchaseOrderRead:
    """Issue a purchase order for raw materials."""
    from src.models import Supplier
    supp = session.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supp:
        raise ValueError("Supplier not found.")
    if quantity < supp.min_order_qty:
        raise ValueError(f"Quantity {quantity} below minimum order quantity {supp.min_order_qty}")
        
    day = get_current_day(session)
    
    # override expected delivery intelligently: today + lead_time_days
    actual_expected_delivery = day + supp.lead_time_days
    
    po = PurchaseOrder(
        supplier_id=supplier_id,
        product_id=product_id,
        quantity=quantity,
        issue_date=day,
        expected_delivery=actual_expected_delivery,
        status=PurchaseOrderStatus.OPEN
    )
    session.add(po)
    session.flush()
    
    log_event(session, EventType.PO_CREATED, day, {"po_id": po.id, "supplier": supplier_id, "qty": quantity})
    session.commit()
    return PurchaseOrderRead.model_validate(po)


def export_state(session: Session) -> Dict[str, Any]:
    """Export full simulation state as JSON-compatible data."""
    # A complete export is a big dump. We export models as JSON dicts.
    from src.models import Product, Supplier, BOM, Inventory
    
    state = {
        "current_day": get_current_day(session),
        "products": [{"id": p.id, "name": p.name, "type": p.type.value} for p in session.query(Product).all()],
        "bom": [{"id": b.id, "finished_product_id": b.finished_product_id, "material_id": b.material_id, "qty": b.quantity} for b in session.query(BOM).all()],
        "suppliers": [{"id": s.id, "name": s.name, "product_id": s.product_id, "cost": s.unit_cost, "lead_time": s.lead_time_days, "min_qty": s.min_order_qty} for s in session.query(Supplier).all()],
        "inventory": [{"product_id": i.product_id, "quantity": i.quantity, "reserved": i.reserved} for i in session.query(Inventory).all()],
        "manufacturing_orders": [{"id": o.id, "product_id": o.product_id, "qty": o.quantity, "status": o.status.value, "created": o.created_date, "start": o.start_date, "completed": o.completed_date} for o in session.query(ManufacturingOrder).all()],
        "purchase_orders": [{"id": p.id, "supplier_id": p.supplier_id, "product_id": p.product_id, "qty": p.quantity, "issue": p.issue_date, "expected": p.expected_delivery, "status": p.status.value} for p in session.query(PurchaseOrder).all()],
        "events": [{"id": e.id, "type": e.type.value, "day": e.sim_date, "details": e.details} for e in session.query(Event).all()]
    }
    return state


def import_state(session: Session, state: Dict[str, Any]) -> None:
    """Import simulation state from JSON data."""
    # Since round trip import/export implies truncating and loading
    # We will reset and manually build the db objects from Dict
    raise NotImplementedError("import_state requires explicit table wiping logic, skipping for now per MVP")
