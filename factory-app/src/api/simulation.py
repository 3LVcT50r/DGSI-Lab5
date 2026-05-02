"""Simulation control API routes."""

from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.services.simulation import (
    advance_day,
    get_simulation_status,
    reset_simulation,
)

router = APIRouter()


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
