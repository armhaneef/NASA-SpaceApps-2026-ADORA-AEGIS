from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.routes import create_app
from app.services import llm_service
from app.services.llm_service import LLMCallError, LLMService


def _settings(*, api_key: str = "test-gemini-key", model: str = "gemini-2.5-flash") -> SimpleNamespace:
    return SimpleNamespace(
        llm_provider="gemini",
        llm_model="",
        llm_api_key="",
        gemini_api_key=api_key,
        gemini_model=model,
        llm_timeout_seconds=60,
        llm_max_output_tokens=120,
        llm_max_retries=1,
    )


def _install_fake_sdk(monkeypatch, generate_content):
    calls: dict[str, object] = {"client": None, "request": None}

    class FakeHttpOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeGenerateContentConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.models = SimpleNamespace(generate_content=self._generate)

        def _generate(self, **kwargs):
            calls["request"] = kwargs
            return generate_content(**kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    google_package = ModuleType("google")
    google_package.__path__ = []
    genai_module = ModuleType("google.genai")
    genai_module.Client = FakeClient
    types_module = ModuleType("google.genai.types")
    types_module.HttpOptions = FakeHttpOptions
    types_module.GenerateContentConfig = FakeGenerateContentConfig
    genai_module.types = types_module
    google_package.genai = genai_module
    monkeypatch.setitem(sys.modules, "google", google_package)
    monkeypatch.setitem(sys.modules, "google.genai", genai_module)
    monkeypatch.setitem(sys.modules, "google.genai.types", types_module)
    return calls


def test_gemini_provider_uses_google_genai_sdk(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings())
    calls = _install_fake_sdk(
        monkeypatch,
        lambda **_kwargs: SimpleNamespace(text="Gemini test answer"),
    )

    service = LLMService()
    assert service.is_available() is True
    assert service.generate("Synthetic question", system_prompt="Stay evidence grounded.") == "Gemini test answer"
    assert calls["client"]["api_key"] == "test-gemini-key"
    assert calls["client"]["http_options"].kwargs == {"timeout": 60_000}
    assert calls["request"]["model"] == "gemini-2.5-flash"
    assert calls["request"]["contents"] == "Synthetic question"
    assert calls["request"]["config"].kwargs == {
        "system_instruction": "Stay evidence grounded.",
        "temperature": 0.2,
        "max_output_tokens": 120,
    }


def test_gemini_provider_requires_api_key(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings(api_key=""))
    service = LLMService()
    assert service.offline is True
    assert service.is_available() is False


def test_gemini_errors_are_sanitized_and_keep_http_status(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings())

    class APIError(Exception):
        code = 429

    calls = _install_fake_sdk(
        monkeypatch,
        lambda **_kwargs: (_ for _ in ()).throw(APIError("private provider response")),
    )

    with pytest.raises(LLMCallError, match="HTTP 429") as error:
        LLMService().generate("Synthetic question")
    assert error.value.status_code == 429
    assert "private provider response" not in str(error.value)
    assert calls["request"]["model"] == "gemini-2.5-flash"


def test_chat_endpoint_reports_gemini_response_as_online(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings())
    calls = _install_fake_sdk(
        monkeypatch,
        lambda **_kwargs: SimpleNamespace(text="Synthetic Gemini-generated answer."),
    )
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/chat",
        json={
            "astronaut_id": "SYNTHETIC-ASTRONAUT-001",
            "question": "Explain the demo. No real sensor readings are available.",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["answer"] == "Synthetic Gemini-generated answer."
    assert response.json()["offline_mode"] is False
    assert calls["request"]["model"] == "gemini-2.5-flash"
