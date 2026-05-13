"""Sales order handling functions."""

from sqlalchemy.orm import Session
from src.models.order import SalesOrder, SalesOrderStatus
from src.schemas.request import SalesOrderCreate
from src.schemas.response import SalesOrderRead
from src.models.event import Event


def create_sales_order(session: Session, order_data: SalesOrderCreate) -> SalesOrderRead:
    """Create a new sales order from a retailer."""
    from src.services.simulation import get_current_day, log_event
    from src.models.event import EventType

    current_day = get_current_day(session)
    
    order = SalesOrder(
        retailer=order_data.retailer,
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        status=SalesOrderStatus.PENDING,
        received_date=current_day,
    )
    session.add(order)
    session.flush()
    
    # Log event
    log_event(
        session, EventType.ORDER_CREATED, current_day,
        {
            "order_id": order.id,
            "retailer": order_data.retailer,
            "product_id": order_data.product_id,
            "qty": order_data.quantity,
        },
    )
    
    session.commit()
    return SalesOrderRead.from_orm(order)


def get_sales_orders(session: Session) -> list[SalesOrderRead]:
    """Get all sales orders."""
    orders = session.query(SalesOrder).all()
    return [SalesOrderRead.from_orm(o) for o in orders]