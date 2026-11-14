from __future__ import annotations

import re
from typing import Any

from app.schemas.alert import MLInputRecord


class InputGuard:
    """Check user and ML inputs before they reach the assistant or RAG layer."""

    @staticmethod
    def validate_question(question: str) -> str:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")
        sanitized = question.strip()
        if len(sanitized) > 2000:
            raise ValueError("Question exceeds supported length.")
        if re.search(r"(?i)ignore previous instructions|system prompt|developer prompt|jailbreak", sanitized):
            raise ValueError("Prompt injection attempts are not allowed in the assistant input.")
        return sanitized

    @staticmethod
    def validate_ml_record(record: dict[str, Any]) -> MLInputRecord:
        return MLInputRecord.model_validate(record)

    @staticmethod
    def validate_astronaut_scope(astronaut_id: str, current_astronaut_id: str) -> None:
        if astronaut_id != current_astronaut_id:
            raise ValueError("Cross-astronaut data access is not permitted without explicit authorization.")
