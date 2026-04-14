import logging
from sqlalchemy.orm import Session
from typing import List

from src.models import Inventory, BOM, Product
from src.schemas import InventoryRead

logger = logging.getLogger(__name__)


def get_inventory_levels(session: Session) -> List[InventoryRead]:
    """Return current inventory quantities for all products."""
    inventory_records = session.query(Inventory).all()
    # Serialize to schemas
    return [
        InventoryRead.model_validate(inv)
        for inv in inventory_records
    ]


def reserve_materials(session: Session, product_id: int, quantity: int) -> bool:
    """
    Reserve raw materials required to start a manufacturing order.
    Returns True if successful, False if insufficient stock.
    """
    # 1. Fetch the BOM for this finished product
    boms = session.query(BOM).filter(BOM.finished_product_id == product_id).all()
    if not boms:
        # If no BOM, technically no materials are needed, but this might be an error state.
        logger.warning(f"Product {product_id} has no BOM.")
        return True
    
    # 2. Check if we have enough stock for all materials
    material_needs = {}
    for bom_item in boms:
        needed_qty = bom_item.quantity * quantity
        material_needs[bom_item.material_id] = needed_qty

    inventory_items = session.query(Inventory).filter(
        Inventory.product_id.in_(material_needs.keys())
    ).with_for_update().all()  # Lock rows

    inv_map = {inv.product_id: inv for inv in inventory_items}

    # Verify all required materials exist and have sufficient free quantity
    for mat_id, needed_qty in material_needs.items():
        inv = inv_map.get(mat_id)
        if not inv:
            logger.warning(f"Material {mat_id} not found in inventory.")
            return False
        
        free_stock = inv.quantity - inv.reserved
        if free_stock < needed_qty:
            logger.warning(
                f"Insufficient stock for material {mat_id}. "
                f"Need: {needed_qty}, Free: {free_stock}"
            )
            return False

    # 3. All good, reserve the materials
    for mat_id, needed_qty in material_needs.items():
        inv = inv_map[mat_id]
        inv.reserved += needed_qty

    return True


def consume_materials(session: Session, product_id: int, quantity: int) -> None:
    """
    Consume inventory that was previously reserved for a released manufacturing order.
    Subtracts the required BOM amounts from both `quantity` and `reserved`.
    """
    boms = session.query(BOM).filter(BOM.finished_product_id == product_id).all()
    material_needs = {bom_item.material_id: bom_item.quantity * quantity for bom_item in boms}

    inventory_items = session.query(Inventory).filter(
        Inventory.product_id.in_(material_needs.keys())
    ).with_for_update().all()
    inv_map = {inv.product_id: inv for inv in inventory_items}

    for mat_id, needed_qty in material_needs.items():
        inv = inv_map.get(mat_id)
        if not inv:
            continue
        
        # We assume the reservation succeeded earlier, so just deduct
        inv.quantity -= needed_qty
        inv.reserved -= needed_qty
        
        # Float math safety
        if inv.quantity < 0: inv.quantity = 0
        if inv.reserved < 0: inv.reserved = 0


def receive_purchase_order(session: Session, product_id: int, quantity: int) -> None:
    """Receive materials from a PO and update inventory."""
    inv = session.query(Inventory).filter(Inventory.product_id == product_id).with_for_update().first()
    if inv:
        inv.quantity += quantity
    else:
        logger.warning(f"PO received for product {product_id} with no inventory record.")
