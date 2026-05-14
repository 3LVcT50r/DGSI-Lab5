"""Sales order handling functions."""

from sqlalchemy.orm import Session
from src.models import (
    Product,
    SalesOrder,
    SalesOrderStatus,
    ManufacturingOrder,
    OrderStatus,
)
from src.schemas.request import SalesOrderCreate
from src.schemas.response import SalesOrderRead


def _resolve_product(session: Session, order_data: SalesOrderCreate) -> Product:
    if order_data.product_id is not None:
        product = session.query(Product).filter(Product.id == order_data.product_id).first()
        if not product:
            raise ValueError(f"Product ID '{order_data.product_id}' not found")
        return product

    if order_data.model:
        product = session.query(Product).filter(Product.name.ilike(order_data.model)).first()
        if not product:
            raise ValueError(f"Product '{order_data.model}' not found")
        return product

    raise ValueError("Either model or product_id must be supplied")


def create_sales_order(session: Session, order_data: SalesOrderCreate) -> SalesOrderRead:
    """Create a new sales order from a retailer."""
    from src.services.simulation import get_current_day, log_event
    from src.models.event import EventType

    product = _resolve_product(session, order_data)
    current_day = get_current_day(session)
    order = SalesOrder(
        retailer=order_data.retailer,
        product_id=product.id,
        quantity=order_data.quantity,
        status=SalesOrderStatus.PENDING,
        received_date=current_day,
    )
    session.add(order)
    session.flush()

    log_event(
        session,
        EventType.ORDER_CREATED,
        current_day,
        {
            "order_id": order.id,
            "retailer": order.retailer,
            "product_id": order.product_id,
            "qty": order.quantity,
        },
    )

    session.commit()
    return SalesOrderRead.from_orm(order)


def get_sales_orders(session: Session) -> list[SalesOrderRead]:
    """Get all sales orders."""
    orders = session.query(SalesOrder).all()
    return [SalesOrderRead.from_orm(o) for o in orders]


def get_sales_order(session: Session, order_id: int) -> SalesOrderRead | None:
    """Get a specific sales order."""
    order = session.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    return SalesOrderRead.from_orm(order) if order else None


def release_sales_order(session: Session, order_id: int) -> SalesOrderRead:
    """Release a retailer sales order to production."""
    from src.services.simulation import get_current_day, log_event
    from src.models.event import EventType

    order = session.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise ValueError("Sales order not found")
    if order.status != SalesOrderStatus.PENDING:
        raise ValueError(f"Order is in status {order.status.value}, cannot release")

    current_day = get_current_day(session)
    order.status = SalesOrderStatus.RELEASED
    order.released_date = current_day

    manufacturing_order = ManufacturingOrder(
        created_date=current_day,
        product_id=order.product_id,
        quantity=order.quantity,
        status=OrderStatus.PENDING,
        sales_order_id=order.id,
    )
    session.add(manufacturing_order)
    session.flush()

    log_event(
        session,
        EventType.ORDER_RELEASED,
        current_day,
        {
            "sales_order_id": order.id,
            "manufacturing_order_id": manufacturing_order.id,
            "retailer": order.retailer,
            "product_id": order.product_id,
            "qty": order.quantity,
        },
    )

    session.commit()
    return SalesOrderRead.from_orm(order)
