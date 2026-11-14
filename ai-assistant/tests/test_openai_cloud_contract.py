from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routes import create_app
from app.services import llm_service
from app.services.llm_service import LLMCallError, LLMService


def _settings(model: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1") -> SimpleNamespace:
    return SimpleNamespace(
        llm_provider="openai_compatible",
        llm_model=model,
        llm_api_key="unit-test-key",
        llm_base_url=base_url,
        llm_timeout_seconds=60,
        llm_max_output_tokens=600,
        llm_max_retries=1,
    )


def _install_fake_openai(monkeypatch, response_factory):
    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.client_kwargs = kwargs
            self.responses = SimpleNamespace(create=response_factory)

    fake_module = SimpleNamespace(OpenAI=FakeOpenAI)
    monkeypatch.setitem(sys.modules, "openai", fake_module)
    return FakeOpenAI


def test_openai_provider_uses_official_responses_sdk(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings())
    response = SimpleNamespace(output_text="Responses API answer")
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return response

    fake_client = _install_fake_openai(monkeypatch, create)

    assert LLMService(provider="openai").generate("Hello AEGIS") == "Responses API answer"
    assert calls == [{
        "model": "gpt-4o-mini",
        "instructions": "You are a cautious, evidence-grounded astronaut health assistant.",
        "input": "Hello AEGIS",
        "max_output_tokens": 600,
        "store": False,
        "temperature": 0.2,
    }]
    # The constructor options are checked without exposing the API key.
    assert fake_client


def test_openai_provider_retries_one_transient_connection_failure(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings())
    attempts = []

    class APIConnectionError(Exception):
        pass

    def create(**kwargs):
        attempts.append(kwargs)
        if len(attempts) == 1:
            raise APIConnectionError("network unavailable")
        return SimpleNamespace(output_text="recovered answer")

    _install_fake_openai(monkeypatch, create)
    assert LLMService(provider="openai").generate("Retry safely") == "recovered answer"
    assert len(attempts) == 2


@pytest.mark.parametrize("status_code", [401, 429, 500])
def test_openai_provider_maps_api_failures_without_leaking_details(monkeypatch, status_code):
    monkeypatch.setattr(llm_service, "settings", _settings())

    class APIError(Exception):
        def __init__(self):
            super().__init__("secret key or response body")
            self.status_code = status_code

    def create(**kwargs):
        raise APIError()

    _install_fake_openai(monkeypatch, create)
    with pytest.raises(LLMCallError, match=str(status_code)) as raised:
        LLMService(provider="openai").generate("Failure test")
    assert "secret key" not in str(raised.value)


def test_openai_provider_maps_timeout(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings())

    class APITimeoutError(Exception):
        pass

    _install_fake_openai(monkeypatch, lambda **kwargs: (_ for _ in ()).throw(APITimeoutError()))
    with pytest.raises(LLMCallError, match="timed out"):
        LLMService(provider="openai").generate("Timeout test")


def test_openai_provider_requires_openai_api_key(monkeypatch):
    config = _settings()
    config.openai_api_key = ""
    config.llm_api_key = ""
    monkeypatch.setattr(llm_service, "settings", config)
    service = LLMService(provider="openai")
    assert service.offline is True
    assert service.is_available() is False


def test_openai_provider_prefers_canonical_key_setting(monkeypatch):
    config = _settings()
    config.openai_api_key = "canonical-key"
    config.llm_api_key = "legacy-key"
    monkeypatch.setattr(llm_service, "settings", config)
    service = LLMService(provider="openai")
    assert service.api_key == "canonical-key"
    assert service.offline is False


def test_openai_v1_root_is_normalized_and_authenticated(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings())
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"choices": [{"message": {"content": "cloud answer"}}]}

    with patch("httpx.post", return_value=response) as post:
        assert LLMService().generate("Hello AEGIS") == "cloud answer"

    assert post.call_args.args[0] == "https://api.openai.com/v1/chat/completions"
    assert post.call_args.kwargs["headers"] == {
        "Authorization": "Bearer unit-test-key",
        "Content-Type": "application/json",
    }
    assert post.call_args.kwargs["json"]["temperature"] == 0.2


@pytest.mark.parametrize("status_code", [400, 404, 500])
def test_cloud_http_errors_keep_status_without_leaking_response(monkeypatch, status_code):
    monkeypatch.setattr(llm_service, "settings", _settings())
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    response = httpx.Response(status_code, request=request, content=b"secret provider details")
    error = httpx.HTTPStatusError("provider error", request=request, response=response)

    with patch("httpx.post", side_effect=error):
        with pytest.raises(LLMCallError, match=str(status_code)) as raised:
            LLMService().generate("Hello AEGIS")

    assert "secret provider details" not in str(raised.value)
    assert raised.value.status_code == status_code


def test_invalid_json_and_empty_answer_are_rejected(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings())
    for body in [ValueError("invalid json"), {"choices": [{"message": {"content": "   "}}]}]:
        response = MagicMock()
        response.raise_for_status.return_value = None
        if isinstance(body, Exception):
            response.json.side_effect = body
        else:
            response.json.return_value = body
        with patch("httpx.post", return_value=response):
            with pytest.raises(LLMCallError, match="response format was invalid"):
                LLMService().generate("Hello AEGIS")


def test_assistant_endpoint_uses_mocked_openai_completion(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings())
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"choices": [{"message": {"content": "Evidence-grounded cloud answer."}}]}
    client = TestClient(create_app())
    payload = {
        "astronaut_id": "SYNTHETIC-ASTRONAUT-001",
        "question": "Explain this synthetic health analysis.",
        "context": {
            "analysis": {
                "analysis_id": 1,
                "analysis_timestamp": "2026-01-01T01:41:00Z",
                "measurement_timestamp": "2026-01-01T01:40:00Z",
                "status": "normal",
                "is_mock": True,
                "anomaly_detected": False,
                "anomaly_score": 0.1,
                "affected_measurements": [],
                "model_version": "test",
                "data_source": "synthetic_example",
                "data_quality": {"status": "valid"},
                "detector_method": "test",
                "sensor_method": "test",
            }
        },
    }

    with patch("httpx.post", return_value=response) as post:
        result = client.post("/api/v1/assistant/respond", json=payload)

    assert result.status_code == 200, result.text
    assert result.json()["answer"] == "Evidence-grounded cloud answer."
    assert result.json()["is_mock"] is False
    assert post.called
