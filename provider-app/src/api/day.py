from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.models import Metric
from src.schemas.response import DayRead
from src.services.provider import (
    advance_day,
    get_current_day,
    reset_simulation,
    update_signal,
)

router = APIRouter()


class SignalUpdate(BaseModel):
    """Today's market signal as resolved by the turn engine."""

    sim_day: int = Field(..., ge=0)
    demand_modifier: float = Field(1.0, ge=0.0)
    supply_modifier: float = Field(1.0, ge=0.0)
    lead_time_modifier: float = Field(1.0, ge=0.0)


class MetricRow(BaseModel):
    sim_day: int
    product_id: int
    product_name: str
    stock_qty: float
    top_tier_price: Optional[float]
    orders_pending: int
    orders_shipped_today: int
    orders_delivered_today: int

    class Config:
        from_attributes = True


@router.post("/day/advance", response_model=DayRead)
def post_advance_day(db: Session = Depends(get_db_session)):
    """Advance the simulation by one day."""
    new_day = advance_day(db)
    return DayRead(current_day=new_day)


@router.get("/day/current", response_model=DayRead)
def get_current_day_endpoint(db: Session = Depends(get_db_session)):
    """Get the current simulated day."""
    current_day = get_current_day(db)
    return DayRead(current_day=current_day)


@router.post("/day/reset")
def post_reset_simulation(db: Session = Depends(get_db_session)):
    """Reset simulation to initial configuration."""
    reset_simulation(db)
    return {"status": "reset"}


@router.post("/signal")
def post_signal(signal: SignalUpdate, db: Session = Depends(get_db_session)):
    """Receive today's market signal from the turn engine.

    Call this at the START of each day, before any agent runs. Modifiers
    persisted here are read by `place_order` and reported in metrics.
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


@router.get("/metrics", response_model=List[MetricRow])
def get_metrics(
    db: Session = Depends(get_db_session),
    sim_day: Optional[int] = Query(None, ge=0),
):
    """Read snapshot rows, optionally filtered to a single day."""
    query = db.query(Metric)
    if sim_day is not None:
        query = query.filter(Metric.sim_day == sim_day)
    return query.order_by(Metric.sim_day, Metric.product_id).all()