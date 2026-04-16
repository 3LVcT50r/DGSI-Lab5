from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from provider_app.config import settings
from provider_app.database import SessionLocal, get_db_session, init_db
from provider_app.schemas import (
    DayStatus,
    OrderCreate,
    OrderRead,
    ProductCatalogRead,
    StockRead,
)
from provider_app.services import (
    advance_day,
    export_state,
    get_catalog,
    get_current_day,
    get_order,
    get_orders,
    get_stock,
    import_state,
    load_seed,
    place_order,
)

app = FastAPI(title="Provider App API", version="0.1.0")


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    with SessionLocal() as session:
        load_seed(session, settings.seed_path)


@app.get("/api/catalog", response_model=List[ProductCatalogRead])
def read_catalog(db=Depends(get_db_session)):
    return get_catalog(db)


@app.get("/api/stock", response_model=List[StockRead])
def read_stock(db=Depends(get_db_session)):
    return get_stock(db)


@app.post("/api/orders", response_model=OrderRead)
def create_order(order: OrderCreate, db=Depends(get_db_session)):
    try:
        return place_order(db, order.buyer, order.product, order.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/orders", response_model=List[OrderRead])
def list_orders(status: Optional[str] = Query(None), db=Depends(get_db_session)):
    return get_orders(db, status)


@app.get("/api/orders/{order_id}", response_model=OrderRead)
def show_order(order_id: int, db=Depends(get_db_session)):
    order = get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.post("/api/day/advance")
def advance_current_day(db=Depends(get_db_session)):
    return advance_day(db)


@app.get("/api/day/current", response_model=DayStatus)
def current_day(db=Depends(get_db_session)):
    return {"current_day": get_current_day(db)}


@app.post("/api/state/import")
def api_import_state(payload: dict, db=Depends(get_db_session)):
    import_state(db, payload)
    return {"status": "imported"}


@app.get("/api/state/export")
def api_export_state(db=Depends(get_db_session)):
    return export_state(db)
