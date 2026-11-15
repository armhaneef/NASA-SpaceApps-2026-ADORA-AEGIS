"""Browser preflights, actual JSON responses, and environment allowlist behavior."""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import load_settings
from app.core.cors import configure_cors

ORIGIN = "http://localhost:5173"


def preflight(client, origin=ORIGIN, method="POST", headers="content-type"):
    return client.options("/health/ingest", headers={
        "Origin": origin, "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": headers,
    })


@pytest.mark.parametrize("method", ["GET", "POST", "PATCH", "DELETE"])
def test_approved_preflight(client, method):
    response = preflight(client, method=method)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert method in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
    assert "origin" in response.headers["vary"].lower()
    assert "access-control-allow-credentials" not in response.headers


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://localhost:5175"])
def test_both_vite_origins_are_approved_by_default(client, origin):
    response = preflight(client, origin=origin)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize("origin", ["http://127.0.0.1:5173", "http://localhost:5174",
                                    "https://localhost:5173", "https://unapproved.example", "null"])
def test_unapproved_origin(client, origin):
    response = preflight(client, origin=origin)
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
    actual = client.get("/health", headers={"Origin": origin})
    assert "access-control-allow-origin" not in actual.headers


def test_denied_method_and_header(client):
    assert preflight(client, method="PUT").status_code == 400
    assert preflight(client, headers="x-unapproved-header").status_code == 400


def test_actual_json_and_errors_are_readable_by_approved_browser(client):
    headers = {"Origin": ORIGIN}
    response = client.get("/health", headers=headers)
    assert response.json() == {"status": "ok"}
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert "access-control-allow-origin" not in client.get("/health").headers
    for path, payload, status in [
        ("/astronauts", {}, 422),
        ("/ai/assistant", {"astronaut_id": "missing", "question": "Explain?"}, 404),
    ]:
        response = client.post(path, json=payload, headers=headers)
        assert response.status_code == status
        assert response.headers["access-control-allow-origin"] == ORIGIN
        assert "detail" in response.json()
    client.post("/astronauts", json={"astronaut_id": "CORS-TEST", "name": "Fictional",
                                   "mission_id": "SIM", "mission_role": "Engineer"})
    response = client.post("/ai/assistant", json={"astronaut_id": "CORS-TEST",
                           "question": "Explain?", "mode": "local"}, headers=headers)
    assert response.status_code == 503
    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_configured_allowlist_replaces_default(monkeypatch):
    monkeypatch.setenv("AEGIS_CORS_ORIGINS", json.dumps(["http://localhost:6000/"]))
    app = FastAPI()
    configure_cors(app, load_settings())
    with TestClient(app) as client:
        response = preflight(client, origin="http://localhost:6000")
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:6000"
        assert preflight(client).status_code == 400


def test_empty_allowlist_disables_cors(monkeypatch):
    monkeypatch.setenv("AEGIS_CORS_ORIGINS", "[]")
    app = FastAPI()
    configure_cors(app, load_settings())
    with TestClient(app) as client:
        response = preflight(client)
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers


def test_default_settings(monkeypatch):
    monkeypatch.delenv("AEGIS_CORS_ORIGINS", raising=False)
    assert load_settings().cors_origins == (ORIGIN, "http://localhost:5175")


@pytest.mark.parametrize("value", ["*", '["*"]', '["http://*.example.com"]',
                                   '["null"]', '"http://localhost:5173"',
                                   '["http://localhost:5173/path"]', '["https://user:pass@example.com"]',
                                   '["http://localhost:5173?query=1"]', '["http://localhost:5173#frag"]',
                                   '[1]', "", "not-json"])
def test_bad_configuration_fails_instead_of_allowing_everything(monkeypatch, value):
    monkeypatch.setenv("AEGIS_CORS_ORIGINS", value)
    with pytest.raises(ValueError):
        load_settings()
