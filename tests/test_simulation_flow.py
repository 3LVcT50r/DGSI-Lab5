from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.config import Settings
from src.database import SessionLocal
from src.main import app
from src.models import Product, Supplier, PurchaseOrder, ManufacturingOrder, SimulationState
from src.services.simulation import (
    advance_day,
    create_purchase_order,
    release_order,
    reset_simulation,
)


def setup_simulation(session: Session):
    reset_simulation(session)


def test_reset_simulation_initializes_state():
    session = SessionLocal()
    try:
        reset_simulation(session)

        sim_state = session.query(SimulationState).first()
        assert sim_state is not None
        assert sim_state.current_day == 0

        product_count = session.query(Product).count()
        assert product_count > 0
    finally:
        session.close()


def test_release_order_fails_without_materials():
    session = SessionLocal()
    try:
        reset_simulation(session)

        finished_product = session.query(Product).filter(Product.type == "finished").first()
        assert finished_product is not None

        mo = ManufacturingOrder(
            created_date=0,
            product_id=finished_product.id,
            quantity=1,
            status="pending",
        )
        session.add(mo)
        session.commit()

        try:
            release_order(session, mo.id)
            assert False, "Expected ValueError when releasing order without materials"
        except ValueError as exc:
            assert "Insufficient materials" in str(exc)
    finally:
        session.close()


def test_create_purchase_order_and_receive_materials():
    session = SessionLocal()
    try:
        reset_simulation(session)

        supplier = session.query(Supplier).first()
        assert supplier is not None

        raw_product = session.query(Product).filter(Product.id == supplier.product_id).first()
        assert raw_product is not None

        po = create_purchase_order(
            session,
            supplier_id=supplier.id,
            product_id=raw_product.id,
            quantity=max(1, supplier.min_order_qty),
            expected_delivery=0,
        )

        assert po.status == "open"
        assert po.expected_delivery == session.query(SimulationState).first().current_day + supplier.lead_time_days

        # Move the simulation forward to the arrival day
        session.query(SimulationState).first().current_day = po.expected_delivery - 1
        session.commit()

        result = advance_day(session)
        assert result["current_day"] == po.expected_delivery

        received_po = session.query(PurchaseOrder).filter(PurchaseOrder.id == po.id).first()
        assert received_po.status == "received"

        inventory = session.query(Product).filter(Product.id == raw_product.id).first().inventory
        assert inventory.quantity == po.quantity
    finally:
        session.close()


def test_advance_day_increments_day_and_generates_demand():
    session = SessionLocal()
    try:
        reset_simulation(session)

        initial_day = session.query(SimulationState).first().current_day
        assert initial_day == 0

        result = advance_day(session)
        assert result["status"] == "advanced"
        assert result["current_day"] == 1

        sim_state = session.query(SimulationState).first()
        assert sim_state.current_day == 1

        orders = session.query(ManufacturingOrder).all()
        assert isinstance(orders, list)
    finally:
        session.close()


def test_api_simulate_status_and_advance():
    client = TestClient(app)

    response = client.post("/api/v1/simulate/reset")
    assert response.status_code == 200

    status_response = client.get("/api/v1/simulate/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["current_day"] == 0

    advance_response = client.post("/api/v1/simulate/advance")
    assert advance_response.status_code == 200
    assert advance_response.json()["current_day"] == 1
