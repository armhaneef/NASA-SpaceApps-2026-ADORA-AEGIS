"""Explicit environment settings without introducing a settings dependency."""

import json
import os

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, TypeAdapter, field_validator


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://localhost:5175")
    assistant_base_url: str | None = None
    assistant_timeout_seconds: float = Field(default=3.0, gt=0, le=30)

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

    assistant_url = os.environ.get("AEGIS_ASSISTANT_URL", "").strip()
    assistant_base_url = None
    if assistant_url:
        url = TypeAdapter(AnyHttpUrl).validate_python(assistant_url)
        if url.username is not None or url.password is not None or url.query is not None or url.fragment is not None:
            raise ValueError("AEGIS_ASSISTANT_URL must not contain credentials, query, or fragment")
        assistant_base_url = str(url).rstrip("/")
    timeout = float(os.environ.get("AEGIS_ASSISTANT_TIMEOUT_SECONDS", "3"))
    return Settings(
        cors_origins=origins,
        assistant_base_url=assistant_base_url,
        assistant_timeout_seconds=timeout,
    )
