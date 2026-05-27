"""Per-day per-product snapshot rows for offline analysis."""

from sqlalchemy import Column, Float, ForeignKey, Integer, String

from src.models.base import Base


class Metric(Base):
    """One row per (sim_day, product_id) captured at the end of each day.

    Captures both stock/price levels and the fulfillment counts for the
    bar chart required by the Week 8 analysis. Counts are scoped to the
    product they were placed against (per-product groupby works).
    """

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    sim_day = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String, nullable=False)

    printer_stock = Column(Float, nullable=False, default=0.0)
    retail_price = Column(Float, nullable=False, default=0.0)

    orders_placed_today = Column(Integer, nullable=False, default=0)
    orders_fulfilled_today = Column(Integer, nullable=False, default=0)
    orders_backordered_today = Column(Integer, nullable=False, default=0)
