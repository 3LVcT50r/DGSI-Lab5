import json

from fastapi.testclient import TestClient
from src.database import SessionLocal
from src.main import app
from src.services.simulation import export_state, import_state, reset_simulation


def test_export_state_contains_required_keys():
    session = SessionLocal()
    try:
        reset_simulation(session)
        state = export_state(session)

        assert state["current_day"] == 0
        assert "products" in state
        assert "bom" in state
        assert "suppliers" in state
        assert "inventory" in state
        assert "manufacturing_orders" in state
        assert "purchase_orders" in state
        assert "events" in state
    finally:
        session.close()


def test_import_state_round_trip():
    session = SessionLocal()
    try:
        reset_simulation(session)
        original_state = export_state(session)

        import_state(session, original_state)
        round_trip_state = export_state(session)

        assert round_trip_state["current_day"] == original_state["current_day"]
        assert len(round_trip_state["products"]) == len(original_state["products"])
        assert len(round_trip_state["bom"]) == len(original_state["bom"])
        assert len(round_trip_state["suppliers"]) == len(original_state["suppliers"])
        assert len(round_trip_state["inventory"]) == len(original_state["inventory"])
        assert len(round_trip_state["manufacturing_orders"]) == len(original_state["manufacturing_orders"])
        assert len(round_trip_state["purchase_orders"]) == len(original_state["purchase_orders"])
        assert len(round_trip_state["events"]) == len(original_state["events"])
    finally:
        session.close()


def test_import_state_api_accepts_exported_json():
    client = TestClient(app)
    response = client.get("/api/v1/state/export")
    assert response.status_code == 200

    exported_state = response.json()
    file_payload = json.dumps(exported_state)

    response = client.post(
        "/api/v1/state/import",
        files={"file": ("state.json", file_payload, "application/json")},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "imported"}


def test_import_state_api_rejects_invalid_payload():
    client = TestClient(app)
    invalid_state = {"invalid": "payload"}
    file_payload = json.dumps(invalid_state)

    response = client.post(
        "/api/v1/state/import",
        files={"file": ("invalid.json", file_payload, "application/json")},
    )
    assert response.status_code == 400
    assert "missing required keys" in response.json()["detail"]
