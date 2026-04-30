"""Tests for the 3D Printer Factory Simulation."""

import sys
import os

# Ensure the project root is on the path so imports work
# even when pytest is invoked without PYTHONPATH set.
sys.path.insert(
    0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from fastapi.testclient import TestClient  # noqa: E402
from src.config import Settings  # noqa: E402
from src.main import app  # noqa: E402


client = TestClient(app)


# ---------------------------------------------------------------
# Settings
# ---------------------------------------------------------------

def test_settings_loads():
    """Verify application settings load correctly."""
    settings = Settings()
    assert settings.app_name == (
        "3D Printer Factory Simulator"
    )


# ---------------------------------------------------------------
# Health
# ---------------------------------------------------------------

def test_app_has_health_endpoint():
    """Verify the /health endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------

def test_simulation_status():
    """Verify /simulate/status returns valid data."""
    response = client.get("/api/v1/simulate/status")
    assert response.status_code == 200
    data = response.json()
    assert "current_day" in data
    assert "pending_orders" in data
    assert "inventory_levels" in data
    assert "open_purchase_orders" in data


def test_advance_day():
    """Verify advancing a day works."""
    response = client.post("/api/v1/simulate/advance")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "advanced"
    assert "current_day" in data


# ---------------------------------------------------------------
# Products
# ---------------------------------------------------------------

def test_list_products():
    """Verify /products returns a list."""
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "id" in data[0]
        assert "name" in data[0]
        assert "type" in data[0]


# ---------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------

def test_list_inventory():
    """Verify /inventory returns a list."""
    response = client.get("/api/v1/inventory")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------
# Orders
# ---------------------------------------------------------------

def test_list_orders():
    """Verify /orders returns a list."""
    response = client.get("/api/v1/orders")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------
# BOM
# ---------------------------------------------------------------

def test_list_bom():
    """Verify /bom returns a list."""
    response = client.get("/api/v1/bom")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------

def test_list_suppliers():
    """Verify /suppliers returns a list."""
    response = client.get("/api/v1/suppliers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------
# Purchase Orders
# ---------------------------------------------------------------

def test_list_purchase_orders():
    """Verify /purchase-orders returns a list."""
    response = client.get("/api/v1/purchase-orders")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------
# Events
# ---------------------------------------------------------------

def test_list_events():
    """Verify /events returns a list."""
    response = client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------
# Export
# ---------------------------------------------------------------

def test_export_state():
    """Verify /state/export returns valid state."""
    response = client.get("/api/v1/state/export")
    assert response.status_code == 200
    data = response.json()
    assert "current_day" in data
    assert "products" in data
    assert "bom" in data
    assert "suppliers" in data
    assert "inventory" in data


# ---------------------------------------------------------------
# Reset (run last)
# ---------------------------------------------------------------

def test_reset_simulation():
    """Verify reset works and day goes back to 0."""
    response = client.post("/api/v1/simulate/reset")
    assert response.status_code == 200
    assert response.json() == {"status": "reset"}

    status = client.get("/api/v1/simulate/status")
    assert status.json()["current_day"] == 0
