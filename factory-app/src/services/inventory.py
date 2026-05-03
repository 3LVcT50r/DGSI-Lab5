"""Inventory management: reservation, consumption, and PO receipt."""

import logging
from sqlalchemy.orm import Session
from typing import List, Tuple

from src.models import Inventory, BOM, Product
from src.schemas import InventoryRead

logger = logging.getLogger(__name__)


def get_inventory_levels(
    session: Session,
) -> List[InventoryRead]:
    """Return current inventory quantities."""
    inventory_records = session.query(Inventory).all()
    return [
        InventoryRead.model_validate(inv)
        for inv in inventory_records
    ]


def set_inventory_stock(
    session: Session,
    product_id: int,
    quantity: float,
    reserved: float = 0.0,
) -> InventoryRead:
    """Set the inventory quantity and reserved stock for a product."""
    inv = session.query(Inventory).filter(
        Inventory.product_id == product_id
    ).first()
    if inv is None:
        inv = Inventory(
            product_id=product_id,
            quantity=quantity,
            reserved=reserved,
        )
        session.add(inv)
    else:
        inv.quantity = quantity
        inv.reserved = reserved

    session.commit()
    return InventoryRead.model_validate(inv)


def initialize_inventory(
    session: Session,
    inventory_items: list[dict],
) -> List[InventoryRead]:
    """Initialize inventory records from a JSON array."""
    updated_items: List[InventoryRead] = []

    for item in inventory_items:
        product_id = int(item["product_id"])
        quantity = float(item["quantity"])
        reserved = float(item.get("reserved", 0.0))

        inv = session.query(Inventory).filter(
            Inventory.product_id == product_id
        ).first()
        if inv is None:
            inv = Inventory(
                product_id=product_id,
                quantity=quantity,
                reserved=reserved,
            )
            session.add(inv)
        else:
            inv.quantity = quantity
            inv.reserved = reserved

        updated_items.append(InventoryRead.model_validate(inv))

    session.commit()
    return updated_items


def reserve_materials(
    session: Session,
    product_id: int,
    quantity: int,
) -> Tuple[bool, List[str]]:
    """Reserve raw materials for a manufacturing order.

    Returns:
        (True, []) if successful.
        (False, [missing_info]) if insufficient stock.
    """
    boms = session.query(BOM).filter(
        BOM.finished_product_id == product_id
    ).all()
    if not boms:
        logger.warning(
            "Product %s has no BOM.", product_id
        )
        return True, []

    material_needs = {}
    for bom_item in boms:
        needed_qty = bom_item.quantity * quantity
        material_needs[bom_item.material_id] = needed_qty

    inventory_items = session.query(Inventory).filter(
        Inventory.product_id.in_(material_needs.keys())
    ).with_for_update().all()

    inv_map = {
        inv.product_id: inv for inv in inventory_items
    }

    products = session.query(Product).filter(
        Product.id.in_(material_needs.keys())
    ).all()
    product_map = {p.id: p.name for p in products}

    missing_materials = []
    for mat_id, needed_qty in material_needs.items():
        inv = inv_map.get(mat_id)
        mat_name = product_map.get(
            mat_id, f"ID {mat_id}"
        )

        if not inv:
            missing_materials.append(
                f"{mat_name} "
                f"(Need {needed_qty}, Have 0)"
            )
            continue

        free_stock = inv.quantity - inv.reserved
        if free_stock < needed_qty:
            missing_materials.append(
                f"{mat_name} "
                f"(Need {needed_qty}, "
                f"Have {free_stock})"
            )

    if missing_materials:
        return False, missing_materials

    for mat_id, needed_qty in material_needs.items():
        inv = inv_map[mat_id]
        inv.reserved += needed_qty

    return True, []


def consume_materials(
    session: Session,
    product_id: int,
    quantity: int,
) -> None:
    """Consume reserved inventory for production."""
    boms = session.query(BOM).filter(
        BOM.finished_product_id == product_id
    ).all()
    material_needs = {
        bom_item.material_id: bom_item.quantity * quantity
        for bom_item in boms
    }

    inventory_items = session.query(Inventory).filter(
        Inventory.product_id.in_(material_needs.keys())
    ).with_for_update().all()
    inv_map = {
        inv.product_id: inv for inv in inventory_items
    }

    for mat_id, needed_qty in material_needs.items():
        inv = inv_map.get(mat_id)
        if not inv:
            continue

        inv.quantity -= needed_qty
        inv.reserved -= needed_qty

        # Float math safety
        if inv.quantity < 0:
            inv.quantity = 0
        if inv.reserved < 0:
            inv.reserved = 0


def receive_purchase_order(
    session: Session,
    product_id: int,
    quantity: int,
) -> None:
    """Receive materials from a PO and update inventory."""
    inv = session.query(Inventory).filter(
        Inventory.product_id == product_id
    ).with_for_update().first()
    if inv:
        inv.quantity += quantity
    else:
        logger.warning(
            "PO received for product %s "
            "with no inventory record.",
            product_id,
        )
