from fastapi.testclient import TestClient
from src.config import Settings
from src.main import app


def test_settings_loads():
    settings = Settings()
    assert settings.app_name == "3D Printer Factory Simulator"


def test_app_has_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
