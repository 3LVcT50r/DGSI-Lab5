from sqlalchemy.orm import Session
from typing import List
from src.models import DailyMetrics
from src.schemas import DailyMetricsRead


def record_daily_metrics(session: Session, day: int, total_inventory: int,
                        pending_orders: int, completed_orders: int,
                        open_purchase_orders: int, production_output: int) -> None:
    """Record daily metrics for historical tracking."""
    # Check if metrics for this day already exist
    existing = session.query(DailyMetrics).filter(DailyMetrics.day == day).first()

    if existing:
        # Update existing record
        existing.total_inventory = total_inventory
        existing.pending_orders = pending_orders
        existing.completed_orders = completed_orders
        existing.open_purchase_orders = open_purchase_orders
        existing.production_output = production_output
    else:
        # Create new record
        metrics = DailyMetrics(
            day=day,
            total_inventory=total_inventory,
            pending_orders=pending_orders,
            completed_orders=completed_orders,
            open_purchase_orders=open_purchase_orders,
            production_output=production_output
        )
        session.add(metrics)

    session.commit()


def get_daily_metrics_history(session: Session, limit: int = 30) -> List[DailyMetricsRead]:
    """Get historical daily metrics."""
    metrics = session.query(DailyMetrics).order_by(DailyMetrics.day.desc()).limit(limit).all()

    return [
        DailyMetricsRead(
            id=m.id,
            day=m.day,
            total_inventory=m.total_inventory,
            pending_orders=m.pending_orders,
            completed_orders=m.completed_orders,
            open_purchase_orders=m.open_purchase_orders,
            production_output=m.production_output,
            created_at=m.created_at
        )
        for m in reversed(metrics)  # Reverse to show chronological order
    ]