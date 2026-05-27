"""Per-day per-product snapshot rows for offline analysis."""

from sqlalchemy import Column, Float, ForeignKey, Integer, String

from src.models.base import Base


class Metric(Base):
    """One row per (sim_day, product_id) captured at the end of each day.

    Day-level aggregates (`orders_pending`, `orders_shipped_today`,
    `orders_delivered_today`) repeat on every row of the same day, so the
    analyzer can pick any single row to read them and group-by `product_id`
    for the per-product series.
    """

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    sim_day = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String, nullable=False)

    stock_qty = Column(Float, nullable=False, default=0.0)
    top_tier_price = Column(Float, nullable=True)

    orders_pending = Column(Integer, nullable=False, default=0)
    orders_shipped_today = Column(Integer, nullable=False, default=0)
    orders_delivered_today = Column(Integer, nullable=False, default=0)
