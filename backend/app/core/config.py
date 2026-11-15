"""Explicit environment settings without introducing a settings dependency."""

import json
import os

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, TypeAdapter, field_validator


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://localhost:5175")
    assistant_url: str | None = "http://127.0.0.1:8002/api/v1/assistant/respond"
    assistant_timeout_seconds: float = Field(default=70.0, gt=0, le=120)

    @field_validator("cors_origins")
    @classmethod
    def validate_origins(cls, origins: tuple[str, ...]) -> tuple[str, ...]:
        normalized = []
        for origin in origins:
            if "*" in origin:
                raise ValueError("Wildcard origins are not allowed")
            url = TypeAdapter(AnyHttpUrl).validate_python(origin)
            if (url.username is not None or url.password is not None
                    or url.path not in (None, "", "/")
                    or url.query is not None or url.fragment is not None):
                raise ValueError("CORS origins must contain only scheme, host and optional port")
            normalized.append(str(url).rstrip("/"))
        return tuple(dict.fromkeys(normalized))


def load_settings() -> Settings:
    """Read a JSON array; [] deliberately disables cross-origin access."""
    raw = os.environ.get("AEGIS_CORS_ORIGINS")
    if raw is None:
        origins = Settings().cors_origins
    else:
        try:
            origins = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("AEGIS_CORS_ORIGINS must be a JSON array of explicit origins") from exc
        if not isinstance(origins, list):
            raise ValueError("AEGIS_CORS_ORIGINS must be a JSON array of explicit origins")

    # The canonical setting is a complete endpoint. Keep the earlier base-URL
    # setting for existing deployments; an explicit blank disables local mode.
    endpoint = os.environ.get("AI_ASSISTANT_URL")
    if endpoint is None:
        legacy_base = os.environ.get("AEGIS_ASSISTANT_URL")
        if legacy_base is None:
            endpoint = Settings().assistant_url
        elif legacy_base.strip():
            endpoint = f"{legacy_base.strip().rstrip('/')}/api/v1/assistant/respond"
        else:
            endpoint = ""
    endpoint = endpoint.strip()
    assistant_url = None
    if endpoint:
        url = TypeAdapter(AnyHttpUrl).validate_python(endpoint)
        if url.username is not None or url.password is not None or url.query is not None or url.fragment is not None:
            raise ValueError("AI_ASSISTANT_URL must not contain credentials, query, or fragment")
        assistant_url = str(url)
    timeout = float(os.environ.get("AI_ASSISTANT_TIMEOUT_SECONDS",
                                   os.environ.get("AEGIS_ASSISTANT_TIMEOUT_SECONDS", "70")))
    return Settings(
        cors_origins=origins,
        assistant_url=assistant_url,
        assistant_timeout_seconds=timeout,
    )
