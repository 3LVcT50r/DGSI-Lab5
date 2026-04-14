import logging
from sqlalchemy.orm import Session
from typing import List, Tuple

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


def reserve_materials(session: Session, product_id: int, quantity: int) -> Tuple[bool, List[str]]:
    """
    Reserve raw materials required to start a manufacturing order.
    Returns (True, []) if successful, (False, [missing_material_names]) if insufficient stock.
    """
    # 1. Fetch the BOM for this finished product
    boms = session.query(BOM).filter(BOM.finished_product_id == product_id).all()
    if not boms:
        logger.warning(f"Product {product_id} has no BOM.")
        return True, []
    
    # 2. Check if we have enough stock for all materials
    material_needs = {}
    for bom_item in boms:
        needed_qty = bom_item.quantity * quantity
        material_needs[bom_item.material_id] = needed_qty

    inventory_items = session.query(Inventory).filter(
        Inventory.product_id.in_(material_needs.keys())
    ).with_for_update().all()  # Lock rows

    inv_map = {inv.product_id: inv for inv in inventory_items}
    
    # Check all materials and compile missing list
    missing_materials = []
    
    # We need product names to make it user friendly
    products = session.query(Product).filter(Product.id.in_(material_needs.keys())).all()
    product_map = {p.id: p.name for p in products}

    # Verify all required materials exist and have sufficient free quantity
    for mat_id, needed_qty in material_needs.items():
        inv = inv_map.get(mat_id)
        mat_name = product_map.get(mat_id, f"ID {mat_id}")
        
        if not inv:
            missing_materials.append(f"{mat_name} (Need {needed_qty}, Have 0)")
            continue
        
        free_stock = inv.quantity - inv.reserved
        if free_stock < needed_qty:
            missing_materials.append(f"{mat_name} (Need {needed_qty}, Have {free_stock})")

    if missing_materials:
        return False, missing_materials

    # 3. All good, reserve the materials
    for mat_id, needed_qty in material_needs.items():
        inv = inv_map[mat_id]
        inv.reserved += needed_qty

    return True, []


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
