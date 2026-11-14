from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgeStore:
    """Lightweight local knowledge storage for approved documents and official NASA references."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parents[2] / "knowledge_base"
        self.sources_path = self.base_dir / "sources.json"
        self.official_sources_path = self.base_dir / "official_nasa_sources.json"
        self.approved_dir = self.base_dir / "approved_documents"
        self.documents: list[dict[str, Any]] = []
        self._load_sources()

    @staticmethod
    def _normalize_document(document: dict[str, Any]) -> dict[str, Any]:
        cleaned = dict(document)
        cleaned["title"] = str(cleaned.get("title", "")).strip()
        cleaned["description"] = str(cleaned.get("description", "")).strip()
        cleaned["content"] = str(cleaned.get("content", "")).strip()
        cleaned["category"] = str(cleaned.get("category", "")).strip()
        cleaned["source_url"] = str(cleaned.get("source_url", "")).strip()
        cleaned["publisher"] = str(cleaned.get("publisher", "Unknown")).strip()
        return cleaned

    @staticmethod
    def _is_valid_citation(document: dict[str, Any]) -> bool:
        title = str(document.get("title", "")).strip()
        url = str(document.get("source_url", "")).strip()
        return bool(title) and url.startswith(("http://", "https://"))

    def _load_sources(self) -> None:
        files_to_load = [self.sources_path, self.official_sources_path]
        loaded: list[dict[str, Any]] = []

        for file_path in files_to_load:
            if not file_path.exists():
                continue
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(data, list):
                loaded.extend(self._normalize_document(item) for item in data if isinstance(item, dict))

        self.documents = [item for item in loaded if self._is_valid_citation(item)]

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        text = (query or "").lower().strip()
        if not text:
            return []

        query_terms = [term for term in text.replace("-", " ").split() if term]
        scored: list[tuple[int, dict[str, Any]]] = []

        for document in self.documents:
            searchable = " ".join([
                str(document.get("title", "")),
                str(document.get("description", "")),
                str(document.get("content", "")),
                str(document.get("category", "")),
                str(document.get("publisher", "")),
            ]).lower()

            matched_terms = sum(1 for term in query_terms if term in searchable)
            if not matched_terms:
                continue

            title_score = 2 if any(term in str(document.get("title", "")).lower() for term in query_terms) else 0
            score = matched_terms + title_score
            scored.append((score, document))

        results = [document for _, document in sorted(scored, key=lambda item: item[0], reverse=True)[: limit]]
        return results

    def status(self) -> dict[str, Any]:
        official_count = sum(1 for document in self.documents if "nasa.gov" in str(document.get("source_url", "")).lower())
        valid_citations = sum(1 for document in self.documents if self._is_valid_citation(document))
        return {
            "knowledge_base_dir": str(self.base_dir),
            "approved_documents_dir": str(self.approved_dir),
            "document_count": len(self.documents),
            "official_source_count": official_count,
            "citation_valid_count": valid_citations,
            "evidence_available": len(self.documents) > 0,
        }
