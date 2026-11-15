from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services import llm_service
from app.services.llm_service import LLMCallError, LLMService


def test_offline_service_handles_questions():
    service = LLMService(provider="offline")
    answer = service.generate("Why was my heart rate flagged?")
    assert "offline" in answer.lower()
    assert "structured" in answer.lower() or "deterministic" in answer.lower()


def _settings(provider: str, model: str, api_key: str = "", base_url: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        llm_provider=provider,
        llm_model=model,
        llm_api_key=api_key,
        llm_base_url=base_url,
        llm_timeout_seconds=7,
    )


def test_openai_compatible_requires_credentials(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings("openai_compatible", "model-test"))

    service = LLMService()

    assert service.offline is True
    assert service.is_available() is False


def test_openai_compatible_with_credentials_uses_chat_completions(monkeypatch):
    monkeypatch.setattr(
        llm_service,
        "settings",
        _settings("openai_compatible", "model-test", "test-key", "https://example.test/v1/chat/completions"),
    )
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"choices": [{"message": {"content": "generated answer"}}]}

    with patch("httpx.post", return_value=response) as post:
        answer = LLMService().generate("Explain the simulated reading.")

    assert answer == "generated answer"
    assert post.call_args.args[0] == "https://example.test/v1/chat/completions"
    assert post.call_args.kwargs["json"]["model"] == "model-test"
    assert post.call_args.kwargs["json"]["messages"][1]["content"] == "Explain the simulated reading."
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert post.call_args.kwargs["timeout"] == 7


def test_gpt54_mini_chat_request_omits_unsupported_sampling_parameters(monkeypatch):
    monkeypatch.setattr(
        llm_service,
        "settings",
        _settings("openai_compatible", "gpt-5.4-mini", "test-key", "https://api.openai.com/v1/chat/completions"),
    )
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"choices": [{"message": {"content": "generated"}}]}

    with patch("httpx.post", return_value=response) as post:
        answer = LLMService().generate("A non-alert question.")

    assert answer == "generated"
    payload = post.call_args.kwargs["json"]
    assert payload == {
        "model": "gpt-5.4-mini",
        "messages": [
            {"role": "system", "content": "You are a cautious, evidence-grounded astronaut health assistant."},
            {"role": "user", "content": "A non-alert question."},
        ],
    }
    assert post.call_args.args[0] == "https://api.openai.com/v1/chat/completions"


@pytest.mark.parametrize("status_code", [401, 403, 429, 500])
def test_openai_http_status_errors_are_reported_without_fallback(monkeypatch, status_code):
    monkeypatch.setattr(llm_service, "settings", _settings("openai_compatible", "gpt-5.4-mini", "test-key"))
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    error = httpx.HTTPStatusError("provider error", request=request, response=response)

    with patch("httpx.post", side_effect=error):
        with pytest.raises(LLMCallError, match=str(status_code)):
            LLMService().generate("A non-alert question.")


def test_openai_timeout_is_reported(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings("openai_compatible", "gpt-5.4-mini", "test-key"))

    with patch("httpx.post", side_effect=httpx.ReadTimeout("timed out")):
        with pytest.raises(LLMCallError, match="timed out"):
            LLMService().generate("A non-alert question.")


def test_ollama_does_not_require_api_key_and_uses_generate_api(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings("ollama", "llama3.1", base_url="http://localhost:11434/"))
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"response": "local answer"}

    service = LLMService()
    with patch("httpx.post", return_value=response) as post:
        answer = service.generate("Summarize synthetic telemetry.")

    assert service.is_available() is True
    assert service.offline is False
    assert answer == "local answer"
    assert post.call_args.args[0] == "http://localhost:11434/api/generate"
    assert post.call_args.kwargs["json"]["model"] == "llama3.1"
    assert post.call_args.kwargs["json"]["stream"] is False
    assert "headers" not in post.call_args.kwargs


def test_compatible_provider_connection_error_is_reported(monkeypatch):
    monkeypatch.setattr(llm_service, "settings", _settings("openai_compatible", "model-test", "test-key"))

    with patch("httpx.post", side_effect=httpx.ConnectError("connection refused")):
        with pytest.raises(LLMCallError, match="request failed"):
            LLMService().generate("test")


@pytest.mark.parametrize("provider_response", [{}, {"choices": []}, {"choices": [{"message": {"content": 7}}]}])
def test_invalid_provider_response_is_rejected(monkeypatch, provider_response):
    monkeypatch.setattr(llm_service, "settings", _settings("openai_compatible", "model-test", "test-key"))
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = provider_response

    with patch("httpx.post", return_value=response):
        with pytest.raises(LLMCallError, match="response format was invalid"):
            LLMService().generate("test")


def test_dotenv_file_loads_openai_configuration_without_printing_credentials(tmp_path):
    (tmp_path / ".env").write_text(
        "LLM_PROVIDER=openai_compatible\n"
        "LLM_MODEL=gpt-5.4-mini\n"
        "LLM_BASE_URL=https://api.openai.com/v1/chat/completions\n"
        "LLM_API_KEY=\n"
        "LLM_TIMEOUT_SECONDS=60\n",
        encoding="utf-8",
    )
    module_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    for key in ("LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL", "LLM_API_KEY", "LLM_TIMEOUT_SECONDS"):
        environment.pop(key, None)
    environment["PYTHONPATH"] = str(module_root)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.core.config import settings; from app.services.llm_service import LLMService; "
            "print(settings.llm_provider, settings.llm_model, settings.llm_base_url, "
            "settings.llm_timeout_seconds, bool(settings.llm_api_key), LLMService().offline)",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == (
        "openai_compatible gpt-5.4-mini https://api.openai.com/v1/chat/completions 60 False True"
    )
    assert "LLM_API_KEY" not in result.stdout


def test_invalid_provider_raises_error():
    service = LLMService(provider="unsupported")
    try:
        service.generate("test")
        assert False, "Expected a provider validation failure"
    except RuntimeError:
        pass
