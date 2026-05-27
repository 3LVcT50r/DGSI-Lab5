from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.config import Settings
from src.models import Metric
from src.schemas.response import DayRead
from src.services.retailer import (
    advance_day,
    get_current_day,
    get_day_summary,
    update_signal,
)

router = APIRouter()


def get_settings() -> Settings:
    return Settings()


class SignalUpdate(BaseModel):
    sim_day: int = Field(..., ge=0)
    demand_modifier: float = Field(1.0, ge=0.0)
    supply_modifier: float = Field(1.0, ge=0.0)
    lead_time_modifier: float = Field(1.0, ge=0.0)
    price_sensitivity: Optional[str] = None


class RetailerMetricRow(BaseModel):
    sim_day: int
    product_id: int
    product_name: str
    printer_stock: float
    retail_price: float
    orders_placed_today: int
    orders_fulfilled_today: int
    orders_backordered_today: int

    class Config:
        from_attributes = True


@router.post("/day/advance", response_model=DayRead)
def post_advance_day(
    db: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    """Advance the simulation by one day."""
    new_day = advance_day(db, settings)
    return DayRead(current_day=new_day)


@router.get("/day/current", response_model=DayRead)
def get_current_day_endpoint(db: Session = Depends(get_db_session)):
    """Get the current retailer simulated day."""
    current_day = get_current_day(db)
    return DayRead(current_day=current_day)


@router.get("/day/summary")
def get_day_summary_endpoint(
    db: Session = Depends(get_db_session),
    day: Optional[int] = Query(None, ge=0),
) -> Dict[str, Any]:
    """Return today's customer-order outcomes for the engine's one-line log."""
    target_day = day if day is not None else get_current_day(db)
    return get_day_summary(db, target_day)


@router.post("/signal")
def post_signal(signal: SignalUpdate, db: Session = Depends(get_db_session)):
    """Receive today's market signal from the turn engine."""
    state = update_signal(
        db,
        sim_day=signal.sim_day,
        demand_modifier=signal.demand_modifier,
        supply_modifier=signal.supply_modifier,
        lead_time_modifier=signal.lead_time_modifier,
        price_sensitivity=signal.price_sensitivity,
    )
    return {
        "sim_day": state.sim_day,
        "demand_modifier": state.demand_modifier,
        "supply_modifier": state.supply_modifier,
        "lead_time_modifier": state.lead_time_modifier,
        "price_sensitivity": state.price_sensitivity,
    }


@router.get("/metrics", response_model=List[RetailerMetricRow])
def get_metrics(
    db: Session = Depends(get_db_session),
    sim_day: Optional[int] = Query(None, ge=0),
):
    """Read snapshot rows, optionally filtered to a single day."""
    query = db.query(Metric)
    if sim_day is not None:
        query = query.filter(Metric.sim_day == sim_day)
    return query.order_by(Metric.sim_day, Metric.product_id).all()
