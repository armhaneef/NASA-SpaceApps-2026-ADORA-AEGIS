from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class AstronautContextStore:
    """Local demo astronaut context used for deterministic alert explanations."""

    def __init__(self, file_path: str | Path | None = None) -> None:
        self.file_path = Path(file_path) if file_path else Path(__file__).resolve().parents[2] / "data" / "demo_astronaut_context.json"
        self._cache: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.file_path.exists():
            return
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        if isinstance(data, dict):
            items = data.get("astronauts", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        for item in items:
            if not isinstance(item, dict):
                continue
            astronaut_id = str(item.get("astronaut_id", "")).strip()
            if astronaut_id:
                self._cache[astronaut_id] = item

    def get(self, astronaut_id: str) -> dict[str, Any] | None:
        if not astronaut_id:
            return None
        astronaut_id = astronaut_id.strip()
        if not astronaut_id:
            return None
        return self._cache.get(astronaut_id)

    def get_default_demo_context(self) -> dict[str, Any] | None:
        return self.get("AST-001")


default_context_store = AstronautContextStore()
