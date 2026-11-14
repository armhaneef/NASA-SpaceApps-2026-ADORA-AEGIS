from __future__ import annotations

from app.core.config import settings


class LLMCallError(RuntimeError):
    pass


class LLMService:
    """Configurable LLM client wrapper with offline fallback."""

    def __init__(self, provider: str | None = None) -> None:
        self.provider = (provider or settings.llm_provider).strip().lower()
        self.model = settings.llm_model
        self.base_url = settings.llm_base_url
        self.api_key = settings.llm_api_key
        self.timeout = settings.llm_timeout_seconds
        self.offline = self.provider in {"offline", "none"} or not self.model or not self.api_key

    def is_available(self) -> bool:
        return not self.offline

    def generate(self, prompt: str, *, system_prompt: str | None = None, temperature: float = 0.2) -> str:
        if self.offline:
            return self.offline_response(prompt)

        if self.provider not in {"openai", "openai_compatible", "ollama"}:
            raise LLMCallError(f"Unsupported provider '{self.provider}'. Supported providers: offline, openai, openai_compatible, ollama.")

        if self.provider == "ollama":
            return self._ollama_call(prompt, system_prompt=system_prompt, temperature=temperature)

        return self._openai_compatible_call(prompt, system_prompt=system_prompt, temperature=temperature)

    def offline_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if any(key in prompt_lower for key in ["heart rate", "sleep", "trending", "what information", "simple language", "digital twin", "microgravity", "sensor"]):
            return (
                "This is the offline demonstration mode. The assistant can explain structured data, summarize the available alert context, "
                "and state limitations without pretending to be a full generative model."
            )
        return "Offline mode is active. The system can only provide bounded, deterministic explanations using the provided data and approved local evidence."

    def _openai_compatible_call(self, prompt: str, *, system_prompt: str | None = None, temperature: float) -> str:
        try:
            import httpx
        except ImportError as exc:
            raise LLMCallError("The OpenAI-compatible client dependency is unavailable.") from exc

        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a cautious, evidence-grounded astronaut health assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        try:
            response = httpx.post(
                self.base_url or "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMCallError("LLM request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMCallError(f"LLM provider returned an error: {exc.response.status_code}.") from exc
        except httpx.HTTPError as exc:
            raise LLMCallError(f"LLM provider request failed: {exc}.") from exc

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMCallError("The LLM response format was invalid.") from exc

    def _ollama_call(self, prompt: str, *, system_prompt: str | None = None, temperature: float) -> str:
        try:
            import httpx
        except ImportError as exc:
            raise LLMCallError("The Ollama client dependency is unavailable.") from exc

        base_url = self.base_url or "http://localhost:11434"
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
            raise LLMCallError(f"Ollama request failed: {exc}.") from exc

        try:
            data = response.json()
            return data["response"]
        except (KeyError, TypeError, ValueError) as exc:
            raise LLMCallError("The Ollama response format was invalid.") from exc
