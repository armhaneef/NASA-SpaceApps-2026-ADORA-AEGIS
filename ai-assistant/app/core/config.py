from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import AnyHttpUrl, TypeAdapter, ValidationError


def _load_local_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    module_dir = Path(__file__).resolve().parents[2]
    candidates = (module_dir / ".env", Path.cwd() / ".env", Path.cwd() / "ai-assistant" / ".env")
    loaded: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved not in loaded and candidate.is_file():
            load_dotenv(candidate, override=False)
            loaded.add(resolved)


def _get_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default
    return value if value > 0 else default


def _has_control_characters(value: str) -> bool:
    return any(ord(char) < 0x20 or 0x7F <= ord(char) <= 0x9F for char in value)


def _get_allowed_origins() -> tuple[str, ...]:
    defaults = (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    configured = os.getenv("AI_ALLOWED_ORIGINS")
    if configured is None:
        return defaults
    error = (
        "AI_ALLOWED_ORIGINS must be a comma-separated list of explicit HTTP(S) origins "
        "with only scheme, host and optional port; empty entries, control characters, "
        "wildcards, credentials, paths, queries and fragments are not allowed."
    )
    # URL parsers and strip() can silently discard controls, including leading SOH.
    if _has_control_characters(configured):
        raise ValueError(error)
    origins = []
    for entry in configured.split(","):
        origin = entry.strip()
        if not origin or "*" in origin or "\\" in origin or any(char.isspace() for char in origin):
            raise ValueError(error)
        try:
            parts = urlsplit(origin)
            url = TypeAdapter(AnyHttpUrl).validate_python(origin)
        except (ValueError, ValidationError):
            # Configuration errors must not echo an accidentally embedded secret.
            raise ValueError(error) from None
        if (parts.scheme not in {"http", "https"} or not parts.netloc
                or parts.netloc.endswith(":") or parts.path not in {"", "/"}
                or parts.username is not None or parts.password is not None
                or url.username is not None or url.password is not None
                or url.path not in {None, "", "/"}
                or url.query is not None or url.fragment is not None):
            raise ValueError(error)
        normalized = str(url).rstrip("/")
        # Host decoding can introduce characters absent from the original entry
        # (for example %2A -> * and %2C -> comma). Validate the final origin too.
        if (_has_control_characters(normalized)
                or any(char.isspace() for char in normalized)
                or any(char in normalized for char in ("*", ",", "\\", "%"))):
            raise ValueError(error)
        origins.append(normalized)
    return tuple(dict.fromkeys(origins))


_load_local_env()


@dataclass(frozen=True)
class Settings:
    app_name: str = "adora-aegis-ai"
    env_file: str | None = None
    llm_provider: str = os.getenv("LLM_PROVIDER", "offline").strip().lower()
    llm_model: str = os.getenv("OPENAI_MODEL", os.getenv("LLM_MODEL", "")).strip()
    llm_base_url: str = os.getenv("LLM_BASE_URL", "").strip()
    # OPENAI_API_KEY is the canonical cloud setting. LLM_API_KEY remains a
    # compatibility fallback for existing OpenAI-compatible/Ollama setups.
    llm_api_key: str = os.getenv("OPENAI_API_KEY", os.getenv("LLM_API_KEY", "")).strip()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", os.getenv("LLM_MODEL", "")).strip()
    openai_base_url: str = os.getenv(
        "OPENAI_BASE_URL", os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    ).strip()
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    llm_timeout_seconds: int = _get_int_env("LLM_TIMEOUT_SECONDS", 60)
    llm_max_output_tokens: int = _get_int_env("LLM_MAX_OUTPUT_TOKENS", 600)
    llm_max_retries: int = _get_int_env("LLM_MAX_RETRIES", 1)
    allowed_origins: tuple[str, ...] = _get_allowed_origins()
    knowledge_base_dir: Path = Path(__file__).resolve().parents[2] / "knowledge_base"
    approved_docs_dir: Path = knowledge_base_dir / "approved_documents"
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    logger_name: str = "aegis.ai"
    max_question_length: int = 2000
    max_payload_size: int = 1_000_000


settings = Settings()
