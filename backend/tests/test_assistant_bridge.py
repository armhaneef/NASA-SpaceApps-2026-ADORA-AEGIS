"""Exercise the real bridge/factory over a fake HTTP transport, never Gemini."""

import json

import httpx
import pytest

from app.core.config import load_settings
from app.services.ai_adapter import get_ai_adapter
from app.schemas.assistant import AssistantProviderRequest
from app.services.errors import AssistantResponseError, AssistantTimeoutError, AssistantUnavailableError


PAYLOAD = AssistantProviderRequest(astronaut_id="AST-BRIDGE", question="Explain synthetic data.", context={"analysis": None})
OUTPUT = {"astronaut_id": "AST-BRIDGE", "answer": "Synthetic test output.",
          "assistant_version": "test-only", "is_mock": False, "limitations": ["Not a diagnosis."]}


def configure(monkeypatch, handler):
    monkeypatch.setenv("AI_ASSISTANT_URL", "http://127.0.0.1:8002/api/v1/assistant/respond")
    client_type = httpx.Client

    def client(**kwargs):
        assert kwargs["trust_env"] is False
        assert kwargs["follow_redirects"] is False
        return client_type(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr("app.services.ai_adapter.httpx.Client", client)
    return get_ai_adapter()


@pytest.mark.parametrize("mock", [False, True])
def test_http_success_preserves_identity_provenance_and_missing_analysis(monkeypatch, mock):
    def handler(request):
        assert json.loads(request.content) == PAYLOAD.model_dump(mode="json")
        assert request.extensions["timeout"]["connect"] == 5
        assert request.extensions["timeout"]["read"] == 70
        assert "authorization" not in request.headers
        return httpx.Response(200, json=OUTPUT | {"is_mock": mock})

    result = configure(monkeypatch, handler).respond(PAYLOAD, "local")
    assert result.is_mock is mock
    assert result.status == ("mock" if mock else "completed")
    assert result.context.analysis is None


@pytest.mark.parametrize("status,error", [(503, AssistantUnavailableError), (504, AssistantTimeoutError),
                                          (302, AssistantUnavailableError), (401, AssistantUnavailableError)])
def test_http_failures_are_sanitized(monkeypatch, status, error):
    adapter = configure(monkeypatch, lambda _: httpx.Response(status, text="PRIVATE provider payload"))
    with pytest.raises(error) as caught:
        adapter.respond(PAYLOAD, "local")
    assert "PRIVATE" not in str(caught.value)


@pytest.mark.parametrize("body", [b"not-json", b"", b"null", b"[]", b'{"answer":""}'])
def test_bad_json_or_incomplete_response_is_502(monkeypatch, body):
    adapter = configure(monkeypatch, lambda _: httpx.Response(200, content=body))
    with pytest.raises(AssistantResponseError):
        adapter.respond(PAYLOAD, "local")


def test_wrong_astronaut_over_http_is_rejected(monkeypatch):
    adapter = configure(monkeypatch, lambda _: httpx.Response(200, json=OUTPUT | {"astronaut_id": "OTHER"}))
    with pytest.raises(AssistantResponseError):
        adapter.respond(PAYLOAD, "local")


def test_mock_never_invokes_http(monkeypatch):
    def forbidden(_):
        pytest.fail("Explicit mock mode contacted HTTP")
    assert configure(monkeypatch, forbidden).respond(PAYLOAD, "mock").is_mock is True


def test_default_endpoint_and_legacy_compatibility(monkeypatch):
    for name in ("AI_ASSISTANT_URL", "AEGIS_ASSISTANT_URL", "AI_ASSISTANT_TIMEOUT_SECONDS", "AEGIS_ASSISTANT_TIMEOUT_SECONDS"):
        monkeypatch.delenv(name, raising=False)
    assert load_settings().assistant_url == "http://127.0.0.1:8002/api/v1/assistant/respond"
    assert load_settings().assistant_timeout_seconds == 70
    monkeypatch.setenv("AEGIS_ASSISTANT_URL", "http://localhost:8002/")
    assert load_settings().assistant_url == "http://localhost:8002/api/v1/assistant/respond"
    monkeypatch.setenv("AI_ASSISTANT_URL", "")
    assert get_ai_adapter().provider is None


@pytest.mark.parametrize("url", ["ftp://localhost/provider", "http://user:secret@localhost:8002/", "http://localhost:8002/?key=secret", "http://localhost:8002/#secret"])
def test_url_cannot_embed_credentials_or_parameters(monkeypatch, url):
    monkeypatch.setenv("AI_ASSISTANT_URL", url)
    with pytest.raises(ValueError):
        load_settings()


@pytest.mark.parametrize("timeout", ["0", "-1", "121", "nan", "inf"])
def test_timeout_is_bounded(monkeypatch, timeout):
    monkeypatch.setenv("AI_ASSISTANT_TIMEOUT_SECONDS", timeout)
    with pytest.raises(ValueError):
        load_settings()
