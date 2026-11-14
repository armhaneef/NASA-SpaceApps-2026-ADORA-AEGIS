from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "adora-aegis-ai"
    env_file: str | None = None
    llm_provider: str = os.getenv("LLM_PROVIDER", "offline").strip().lower()
    llm_model: str = os.getenv("LLM_MODEL", "").strip()
    llm_base_url: str = os.getenv("LLM_BASE_URL", "").strip()
    llm_api_key: str = os.getenv("LLM_API_KEY", "").strip()
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    knowledge_base_dir: Path = Path(__file__).resolve().parents[2] / "knowledge_base"
    approved_docs_dir: Path = knowledge_base_dir / "approved_documents"
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    logger_name: str = "aegis.ai"
    max_question_length: int = 2000
    max_payload_size: int = 1_000_000


settings = Settings()
