from __future__ import annotations

import time

from app.core.config import settings


DEFAULT_OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
SUPPORTED_PROVIDERS = {"offline", "none", "openai", "openai_compatible", "ollama"}


class LLMCallError(RuntimeError):
    """Safe, provider-neutral error raised for a failed model request."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LLMService:
    """Configurable LLM client wrapper with offline fallback."""

    def __init__(self, provider: str | None = None) -> None:
        self.provider = (provider or settings.llm_provider).strip().lower()
        if self.provider == "openai":
            self.model = (getattr(settings, "openai_model", None) or settings.llm_model or "").strip()
            self.api_key = (
                getattr(settings, "openai_api_key", None) or settings.llm_api_key or ""
            ).strip()
            self.base_url = self._normalise_openai_base_url(
                getattr(settings, "openai_base_url", None)
                or getattr(settings, "llm_base_url", None)
                or "https://api.openai.com/v1"
            )
        else:
            self.model = (settings.llm_model or "").strip()
            self.api_key = (settings.llm_api_key or "").strip()
            configured_base_url = (settings.llm_base_url or "").strip()
            self.base_url = self._normalise_base_url(configured_base_url)
        self.timeout = settings.llm_timeout_seconds
        self.max_output_tokens = getattr(settings, "llm_max_output_tokens", 600)
        self.max_retries = min(max(getattr(settings, "llm_max_retries", 1), 0), 2)
        if self.provider in {"offline", "none"}:
            self.offline = True
        elif self.provider == "ollama":
            self.base_url = configured_base_url.rstrip("/") or "http://localhost:11434"
            self.offline = not self.model
        elif self.provider in {"openai", "openai_compatible"}:
            self.offline = not self.model or not self.api_key
        else:
            self.offline = False

    def is_available(self) -> bool:
        return self.provider in {"openai", "openai_compatible", "ollama"} and not self.offline

    def generate(self, prompt: str, *, system_prompt: str | None = None, temperature: float = 0.2) -> str:
        if self.provider not in SUPPORTED_PROVIDERS:
            raise LLMCallError(
                f"Unsupported provider '{self.provider}'. Supported providers: offline, openai, openai_compatible, ollama."
            )
        if self.offline:
            return self.offline_response(prompt)

        if self.provider == "ollama":
            return self._ollama_call(prompt, system_prompt=system_prompt, temperature=temperature)

        if self.provider == "openai":
            return self._responses_call(prompt, system_prompt=system_prompt, temperature=temperature)

        return self._openai_compatible_call(prompt, system_prompt=system_prompt, temperature=temperature)

    @staticmethod
    def _normalise_openai_base_url(value: str) -> str:
        base_url = value.strip().rstrip("/")
        if base_url.endswith("/chat/completions"):
            return base_url[: -len("/chat/completions")]
        if base_url.endswith("/responses"):
            return base_url[: -len("/responses")]
        return base_url or "https://api.openai.com/v1"

    @staticmethod
    def _normalise_base_url(value: str | None) -> str:
        """Accept either a full chat endpoint or an OpenAI-compatible /v1 root."""
        base_url = (value or "").strip().rstrip("/")
        if not base_url:
            return DEFAULT_OPENAI_CHAT_COMPLETIONS_URL
        if base_url.endswith("/v1"):
            return f"{base_url}/chat/completions"
        return base_url

    @staticmethod
    def _supports_temperature(model: str) -> bool:
        """Reasoning models reject sampling controls; standard chat models accept them."""
        lowered = model.strip().lower()
        return not lowered.startswith(("gpt-5", "o1", "o3", "o4"))

    def _responses_call(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        """Call OpenAI's official Responses API without exposing provider details."""
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMCallError(
                "The official OpenAI SDK is not installed. Install requirements.txt before enabling the openai provider."
            ) from exc

        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=0,
            )
        except Exception as exc:
            raise LLMCallError("The OpenAI client could not be initialized.") from exc

        request = {
            "model": self.model,
            "instructions": system_prompt or "You are a cautious, evidence-grounded astronaut health assistant.",
            "input": prompt,
            "max_output_tokens": self.max_output_tokens,
            # Do not retain sensitive simulated health context server-side.
            "store": False,
        }
        if self._supports_temperature(self.model):
            request["temperature"] = temperature

        for attempt in range(self.max_retries + 1):
            try:
                response = client.responses.create(**request)
                answer = getattr(response, "output_text", None)
                if not isinstance(answer, str) or not answer.strip():
                    raise LLMCallError("The OpenAI Responses API returned an empty answer.")
                return answer.strip()
            except LLMCallError:
                raise
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)
                class_name = exc.__class__.__name__
                retryable = class_name in {
                    "APIConnectionError",
                    "APITimeoutError",
                    "RateLimitError",
                    "InternalServerError",
                } or status_code in {429, 500, 502, 503, 504}
                if retryable and attempt < self.max_retries:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                if status_code in {400, 401, 403, 404, 429, 500, 502, 503, 504}:
                    raise LLMCallError(
                        f"OpenAI Responses API returned HTTP {status_code}.",
                        status_code=status_code,
                    ) from exc
                if class_name == "APITimeoutError":
                    raise LLMCallError("OpenAI Responses API request timed out.") from exc
                if class_name == "APIConnectionError":
                    raise LLMCallError("OpenAI Responses API connection failed.") from exc
                raise LLMCallError("OpenAI Responses API request failed.") from exc

        raise LLMCallError("OpenAI Responses API request failed.")

    def offline_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if any(key in prompt_lower for key in ["heart rate", "sleep", "trending", "what information", "simple language", "digital twin", "microgravity", "sensor"]):
            return (
                "This is the offline demonstration mode. The assistant can explain structured data, summarize the available alert context, "
                "and state limitations without pretending to be a full generative model."
            )
        return "Offline mode is active. The system can only provide bounded, deterministic explanations using the provided data and approved local evidence."

    def _openai_compatible_call(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        try:
            import httpx
        except ImportError as exc:
            raise LLMCallError("The OpenAI-compatible client dependency is unavailable.") from exc

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        } if self.api_key else {"Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a cautious, evidence-grounded astronaut health assistant."},
                {"role": "user", "content": prompt},
            ],
        }
        if self._supports_temperature(self.model):
            payload["temperature"] = temperature
        try:
            response = httpx.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMCallError("LLM request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            status_code = getattr(exc.response, "status_code", None)
            if isinstance(status_code, int):
                raise LLMCallError(f"LLM provider returned HTTP {status_code}.", status_code=status_code) from exc
            raise LLMCallError("LLM provider returned an HTTP error.") from exc
        except httpx.HTTPError as exc:
            raise LLMCallError("LLM provider request failed.") from exc

        try:
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("empty or non-text completion")
            return answer.strip()
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMCallError("The LLM response format was invalid.") from exc

    def _ollama_call(self, prompt: str, *, system_prompt: str | None = None, temperature: float) -> str:
        try:
            import httpx
        except ImportError as exc:
            raise LLMCallError("The Ollama client dependency is unavailable.") from exc

        base_url = (self.base_url or "http://localhost:11434").rstrip("/")
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "You are a cautious, evidence-grounded astronaut health assistant.",
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            response = httpx.post(f"{base_url}/api/generate", json=payload, timeout=self.timeout)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMCallError("Ollama request timed out.") from exc
        except httpx.HTTPError as exc:
            raise LLMCallError("Ollama request failed.") from exc

        try:
            data = response.json()
            answer = data["response"]
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("empty or non-text response")
            return answer.strip()
        except (KeyError, TypeError, ValueError) as exc:
            raise LLMCallError("The Ollama response format was invalid.") from exc
