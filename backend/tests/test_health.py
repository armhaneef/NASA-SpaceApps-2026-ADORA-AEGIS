"""Check the public Phase 1 contract and generated API documentation."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_documentation_exposes_health() -> None:
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 200
        response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "get" in response.json()["paths"]["/health"]
