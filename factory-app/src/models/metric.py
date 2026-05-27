"""Per-day per-product snapshot rows for offline analysis."""

from sqlalchemy import Column, Float, ForeignKey, Integer, String

from src.models.base import Base


class Metric(Base):
    """One row per (sim_day, product_id) captured at the end of each day.

    `product_type` distinguishes raw materials from finished printers so the
    inventory chart can split the two stacks. Day-level aggregates
    (`sales_orders_pending`, `sales_orders_completed_today`,
    `capacity_utilisation_pct`) repeat on every row of the same day.
    """

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    sim_day = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String, nullable=False)
    product_type = Column(String, nullable=False)  # "raw" | "finished"

    stock_qty = Column(Float, nullable=False, default=0.0)
    wholesale_price = Column(Float, nullable=True)

    sales_orders_pending = Column(Integer, nullable=False, default=0)
    sales_orders_completed_today = Column(Integer, nullable=False, default=0)
    capacity_utilisation_pct = Column(Float, nullable=False, default=0.0)
