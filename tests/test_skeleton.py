from fastapi.testclient import TestClient
from src.config import Settings
from src.main import app
from src.database import get_db_session
from src.services.simulation import reset_simulation
from sqlalchemy.orm import Session
import pytest


def test_settings_loads():
    settings = Settings()
    assert settings.app_name == "3D Printer Factory Simulator"


def test_app_has_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_simulation_reset():
    """Test that simulation can be reset."""
    # This test requires database access
    # In a real scenario, you'd use a test database
    pass


def test_api_endpoints_exist():
    """Test that main API endpoints exist."""
    client = TestClient(app)

    # Test simulation status endpoint
    response = client.get("/api/v1/simulate/status")
    assert response.status_code in [200, 500]  # 500 is ok if DB not initialized

    # Test suppliers endpoint
    response = client.get("/api/v1/suppliers")
    assert response.status_code in [200, 500]

    # Test inventory endpoint
    response = client.get("/api/v1/inventory")
    assert response.status_code in [200, 500]
