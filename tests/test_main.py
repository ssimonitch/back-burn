"""Test the main FastAPI application."""

from fastapi.testclient import TestClient

from main import app


def test_root_endpoint() -> None:
    """Test the root endpoint returns expected data."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello World"
    assert data["app"] == "Slow Burn AI Fitness Companion"


def test_health_endpoint() -> None:
    """Test the health check endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
