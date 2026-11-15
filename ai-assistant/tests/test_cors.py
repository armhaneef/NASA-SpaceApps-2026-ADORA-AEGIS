"""Explicit origin validation and real ASGI CORS responses; no model requests."""

from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.core.config import _get_allowed_origins


def test_unset_origins_preserve_explicit_development_defaults(monkeypatch):
    monkeypatch.delenv("AI_ALLOWED_ORIGINS", raising=False)
    assert _get_allowed_origins() == (
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5173", "http://127.0.0.1:5173",
    )


@pytest.mark.parametrize("value", [
    "*", "http://*.example.com", "https://example.com,*",
    "", " ", ",", "http://localhost:5173,", ",http://localhost:5173",
    "http://localhost:5173,,http://localhost:5175", "null", "localhost:5173",
    "ftp://localhost:5173", "http://", "https:///example.com", "http:localhost",
    "http://local host:5173", "http://localhost:65536", "http://localhost:",
    "https://example.com/path", "https://example.com//", "https://example.com?",
    "https://example.com?token=QA_PRIVATE_SENTINEL", "https://example.com#",
    "http://user:QA_PRIVATE_SENTINEL@localhost:5173", "http://@localhost:5173",
    "http://localhost\\", "http://local\nhost:5173",
])
def test_invalid_origin_lists_fail_without_echoing_values(monkeypatch, value):
    monkeypatch.setenv("AI_ALLOWED_ORIGINS", value)
    with pytest.raises(ValueError, match="AI_ALLOWED_ORIGINS") as caught:
        _get_allowed_origins()
    assert "QA_PRIVATE_SENTINEL" not in str(caught.value)


@pytest.mark.parametrize("value", [
    "http://%2A.example.test:5173", "http://%2a.example.test:5173",
    "http://localhost%2Cevil.example.test:5173", "http://localhost%2cevil.example.test:5173",
    "\x01http://localhost:5173", "http://localhost:5173\x01",
    "http://local\x01host:5173", "http://localhost:5173\t",
    "\nhttp://localhost:5173", "http://localhost:5173\r",
    "\x7fhttp://localhost:5173", "http://localhost:5173\x85",
    "http://localhost:5173,\x01http://127.0.0.1:5175",
    "http://localhost:5173,http://%2A.example.test:5173",
    "http://%252A.example.test:5173", "http://localhost%252Cevil.example.test:5173",
    "http://local%01host:5173", "http://local%0Ahost:5173",
    "http://localhost%2Fevil.example.test:5173", "http://localhost%5Cevil.example.test:5173",
    "http://localhost%40evil.example.test:5173",
    "http://localhost:%35%31%37%33", "http://localhost:+5173",
    "http://localhost:5173/%2e", "http://localhost:5173/%2F",
    "http://localhost:5173?%23", "http://localhost:5173#%3F",
])
def test_normalization_cannot_hide_prohibited_origin_characters(monkeypatch, value):
    monkeypatch.setenv("AI_ALLOWED_ORIGINS", value)
    with pytest.raises(ValueError, match="AI_ALLOWED_ORIGINS"):
        _get_allowed_origins()


@pytest.mark.parametrize("value,expected", [
    ("http://localhost:5173", ("http://localhost:5173",)),
    ("http://localhost:5175", ("http://localhost:5175",)),
    ("http://localhost:5176", ("http://localhost:5176",)),
    ("http://127.0.0.1:5173", ("http://127.0.0.1:5173",)),
    ("http://[::1]:5173", ("http://[::1]:5173",)),
    ("https://demo.example.test", ("https://demo.example.test",)),
    (" http://localhost:5173/ , http://localhost:5175 ",
     ("http://localhost:5173", "http://localhost:5175")),
    ("http://localhost:5173,http://localhost:5173/", ("http://localhost:5173",)),
    ("HTTP://LOCALHOST:5173/", ("http://localhost:5173",)),
    ("hTtPs://Example.Test:443/", ("https://example.test",)),
    ("http://localhost:80/", ("http://localhost",)),
    ("http://LOCALHOST:05173/", ("http://localhost:5173",)),
    ("http://local%68ost:5173", ("http://localhost:5173",)),
    ("http://%31%32%37.0.0.1:5173", ("http://127.0.0.1:5173",)),
    ("http://[0:0:0:0:0:0:0:1]:5173/", ("http://[::1]:5173",)),
    ("http://localhost%2Eexample.test:5173", ("http://localhost.example.test:5173",)),
])
def test_valid_explicit_origins_are_normalized(monkeypatch, value, expected):
    monkeypatch.setenv("AI_ALLOWED_ORIGINS", value)
    assert _get_allowed_origins() == expected


@pytest.fixture
def cors_client(monkeypatch):
    monkeypatch.setenv("AI_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5175")
    monkeypatch.setattr(routes, "settings", replace(
        routes.settings, allowed_origins=_get_allowed_origins(),
    ))
    with TestClient(routes.create_app()) as client:
        yield client


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://localhost:5175"])
def test_explicit_origins_allow_json_preflight_without_credentials(cors_client, origin):
    response = cors_client.options("/api/v1/chat", headers={
        "Origin": origin, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-credentials" not in response.headers
    actual = cors_client.get("/api/v1/demo", headers={"Origin": origin})
    assert actual.status_code == 200
    assert actual.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-credentials" not in actual.headers


@pytest.mark.parametrize("origin", [
    "https://unapproved.example", "null", "http://localhost:5176",
    "http://127.0.0.1:5175", "https://localhost:5173",
])
def test_unauthorized_origins_are_rejected(cors_client, origin):
    response = cors_client.options("/api/v1/chat", headers={
        "Origin": origin, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
    actual = cors_client.get("/api/v1/demo", headers={"Origin": origin})
    assert "access-control-allow-origin" not in actual.headers
    assert "access-control-allow-credentials" not in actual.headers


@pytest.mark.parametrize("value", [
    "*", "http://%2A.example.test:5173",
    "http://localhost%2Cevil.example.test:5173", "\x01http://localhost:5173",
])
def test_invalid_cors_fails_during_application_import(value):
    environment = os.environ.copy()
    environment["AI_ALLOWED_ORIGINS"] = value
    result = subprocess.run(
        [sys.executable, "-B", "-c",
         "import dotenv; dotenv.load_dotenv = lambda *args, **kwargs: False; import app.main"],
        cwd=Path(__file__).resolve().parents[1], env=environment,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "ValueError: AI_ALLOWED_ORIGINS" in result.stderr
