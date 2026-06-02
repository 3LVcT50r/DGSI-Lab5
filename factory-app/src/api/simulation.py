"""Simulation control API routes."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.models import Metric
from src.services.simulation import (
    advance_day,
    get_simulation_status,
    reset_simulation,
    get_capacity_status,
    update_signal,
)

router = APIRouter()


class SignalUpdate(BaseModel):
    """Today's market signal as resolved by the turn engine."""

    sim_day: int = Field(..., ge=0)
    demand_modifier: float = Field(1.0, ge=0.0)
    supply_modifier: float = Field(1.0, ge=0.0)
    lead_time_modifier: float = Field(1.0, ge=0.0)


class FactoryMetricRow(BaseModel):
    sim_day: int
    product_id: int
    product_name: str
    product_type: str
    stock_qty: float
    wholesale_price: Optional[float]
    sales_orders_pending: int
    sales_orders_completed_today: int
    capacity_utilisation_pct: float

    class Config:
        from_attributes = True


@router.get(
    "/simulate/status",
    response_model=Dict[str, Any],
)
def read_simulation_status(
    db: Session = Depends(get_db_session),
):
    """Get current simulation status."""
    status = get_simulation_status(db)
    return status.model_dump()


@router.post("/simulate/advance")
async def post_advance_day(
    db: Session = Depends(get_db_session),
):
    """Advance the simulated calendar by one day."""
    return await advance_day(db)


@router.post("/simulate/reset")
def post_reset_simulation(
    db: Session = Depends(get_db_session),
):
    """Reset simulation to initial configuration."""
    reset_simulation(db)
    return {"status": "reset"}


@router.get("/capacity")
def get_capacity(db: Session = Depends(get_db_session)):
    """Get daily capacity and utilisation."""
    return get_capacity_status(db)


@router.post("/signal")
def post_signal(signal: SignalUpdate, db: Session = Depends(get_db_session)):
    """Receive today's market signal from the turn engine.

    Stored for observability and so the manufacturer agent prompt can see
    a consistent view of the active scenario event across days.
    """
    state = update_signal(
        db,
        sim_day=signal.sim_day,
        demand_modifier=signal.demand_modifier,
        supply_modifier=signal.supply_modifier,
        lead_time_modifier=signal.lead_time_modifier,
    )
    return {
        "sim_day": state.sim_day,
        "demand_modifier": state.demand_modifier,
        "supply_modifier": state.supply_modifier,
        "lead_time_modifier": state.lead_time_modifier,
    }


@router.get("/metrics", response_model=List[FactoryMetricRow])
def get_metrics(
    db: Session = Depends(get_db_session),
    sim_day: Optional[int] = Query(None, ge=0),
):
    """Read snapshot rows, optionally filtered to a single day."""
    query = db.query(Metric)
    if sim_day is not None:
        query = query.filter(Metric.sim_day == sim_day)
    return query.order_by(Metric.sim_day, Metric.product_id).all()
