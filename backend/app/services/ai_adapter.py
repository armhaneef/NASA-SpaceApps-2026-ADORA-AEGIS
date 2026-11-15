"""Replaceable assistant transport; Member 3 owns assistant content and safety."""

import json
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import load_settings
from app.schemas.assistant import AssistantProviderRequest, AssistantProviderResponse
from app.schemas.assistant import AssistantResponse
from app.services.errors import AssistantResponseError, AssistantTimeoutError, AssistantUnavailableError


class AIAdapter:
    """Synchronous local-provider draft: callable(JSON dict) -> JSON dict."""

    def __init__(self, provider: Callable[[dict], dict] | None = None):
        self.provider = provider

    def respond(self, request: AssistantProviderRequest, mode: str) -> AssistantResponse:
        if mode == "mock":
            output = AssistantProviderResponse(
                astronaut_id=request.astronaut_id,
                answer="MOCK: The assistant is not connected. This is a development "
                       "placeholder; no question interpretation or health assessment was performed.",
                assistant_version="backend-assistant-mock-1.0", is_mock=True,
                limitations=["No AI model or knowledge retrieval was invoked.",
                             "This placeholder provides no medical advice."],
            )
        elif mode == "local":
            if self.provider is None:
                raise AssistantUnavailableError(
                    "Assistant provider is not configured. Use mode=mock explicitly or "
                    "connect Member 3's approved provider through get_ai_adapter."
                )
            try:
                raw = self.provider(deepcopy(request.model_dump(mode="json")))
            except TimeoutError as exc:
                raise AssistantTimeoutError("Assistant provider timed out; retry later") from exc
            except Exception as exc:
                raise AssistantUnavailableError("Assistant provider failed; retry later") from exc
            try:
                # Strict JSON also rejects nonfinite numbers in unexpected fields.
                raw = json.loads(json.dumps(raw, allow_nan=False))
                output = AssistantProviderResponse.model_validate(raw)
                if output.astronaut_id != request.astronaut_id:
                    raise ValueError("Assistant response belongs to another astronaut")
            except Exception as exc:
                raise AssistantResponseError("Assistant provider returned an invalid response") from exc
        else:
            raise ValueError("Unsupported assistant mode")
        return AssistantResponse(
            **output.model_dump(), response_timestamp=datetime.now(timezone.utc),
            mode=mode, status="mock" if output.is_mock else "completed",
            data_source="backend_mock" if mode == "mock" else "configured_local_provider",
            context=request.context.model_copy(deep=True),
        )


def _member3_provider(base_url: str, timeout: float) -> Callable[[dict], dict]:
    """Call Member 3's existing backend-compatible route over localhost HTTP."""
    endpoint = f"{base_url.rstrip('/')}/api/v1/assistant/respond"

    def call(payload: dict) -> dict:
        request = Request(
            endpoint,
            data=json.dumps(payload, allow_nan=False).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
                return json.loads(raw)
        except HTTPError as exc:
            raise RuntimeError(f"Member 3 assistant returned HTTP {exc.code}") from exc
        except TimeoutError as exc:
            raise TimeoutError("Member 3 assistant request failed") from exc
        except URLError as exc:
            raise RuntimeError("Member 3 assistant service is unavailable") from exc

    return call


def get_ai_adapter() -> AIAdapter:
    """Use Member 3's fixed local endpoint only when explicitly configured."""
    settings = load_settings()
    provider = (
        _member3_provider(settings.assistant_base_url, settings.assistant_timeout_seconds)
        if settings.assistant_base_url else None
    )
    return AIAdapter(provider=provider)
