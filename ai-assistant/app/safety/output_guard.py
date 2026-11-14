from __future__ import annotations

from typing import Any


class OutputGuard:
    """Validate output before it is returned to the user or frontend."""

    @staticmethod
    def validate_response(payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("Assistant response must be a JSON object.")
        for key in ["answer", "uncertainty", "status"]:
            if key not in payload:
                raise ValueError(f"Output response is missing required field '{key}'.")
        if "answer" in payload and not isinstance(payload["answer"], str):
            raise ValueError("Output answer must be a string.")
        if "sources" in payload and payload["sources"] is None:
            payload["sources"] = []
        return payload
