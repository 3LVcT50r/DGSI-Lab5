from sqlalchemy.orm import Session
from typing import List
from src.schemas import InventoryRead
from src.models import Inventory, Product, BOM


def get_inventory_levels(session: Session) -> List[InventoryRead]:
    """Return current inventory quantities for all products."""
    inventories = session.query(Inventory).join(Product).all()
    return [
        InventoryRead(
            product_id=inv.product_id,
            quantity=inv.quantity
        )
        for inv in inventories
    ]


def get_inventory_for_product(session: Session, product_id: int) -> int:
    """Get current inventory quantity for a specific product."""
    inventory = session.query(Inventory).filter(Inventory.product_id == product_id).first()
    return inventory.quantity if inventory else 0


def update_inventory(session: Session, product_id: int, quantity_change: int) -> None:
    """Update inventory quantity for a product."""
    inventory = session.query(Inventory).filter(Inventory.product_id == product_id).first()
    if inventory:
        inventory.quantity += quantity_change
        session.commit()


def get_bom_for_product(session: Session, product_id: int) -> List[dict]:
    """Get bill of materials for a finished product."""
    bom_entries = session.query(BOM).filter(BOM.finished_product_id == product_id).all()
    return [
        {
            "material_id": entry.material_id,
            "material_name": entry.material.name,
            "quantity": entry.quantity
        }
        for entry in bom_entries
    ]


def check_materials_available(session: Session, product_id: int, quantity: int) -> bool:
    """Check if materials are available to produce the given quantity of product."""
    bom = get_bom_for_product(session, product_id)
    for material in bom:
        required = material["quantity"] * quantity
        available = get_inventory_for_product(session, material["material_id"])
        if available < required:
            return False
    return True


def reserve_materials(session: Session, product_id: int, quantity: int) -> bool:
    """Reserve raw materials required to start a manufacturing order."""
    if not check_materials_available(session, product_id, quantity):
        return False

    bom = get_bom_for_product(session, product_id)
    for material in bom:
        required = material["quantity"] * quantity
        update_inventory(session, material["material_id"], -required)

    return True


def consume_materials(session: Session, order_id: int) -> None:
    """Consume inventory for a released manufacturing order."""
    # For now, materials are already consumed when order is released
    # This could be enhanced to consume materials progressively during production
    pass
