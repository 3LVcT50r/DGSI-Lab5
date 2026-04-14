from sqlalchemy.orm import Session
from typing import List
from src.schemas import InventoryRead


def get_inventory_levels(session: Session) -> List[InventoryRead]:
    """Return current inventory quantities for all products."""
    raise NotImplementedError("get_inventory_levels is not implemented yet")


def reserve_materials(session: Session, product_id: int, quantity: int) -> bool:
    """Reserve raw materials required to start a manufacturing order."""
    raise NotImplementedError("reserve_materials is not implemented yet")


def consume_materials(session: Session, order_id: int) -> None:
    """Consume inventory for a released manufacturing order."""
    raise NotImplementedError("consume_materials is not implemented yet")
