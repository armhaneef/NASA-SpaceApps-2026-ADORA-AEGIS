from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.schemas.alert import MLInputRecord
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.alert_explainer import AlertExplainer
from app.services.astronaut_context import default_context_store
from app.services.context_builder import ContextBuilder
from app.services.llm_service import LLMService

logger = get_logger(__name__)


class HealthAssistant:
    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm_service = llm_service or LLMService()

    def answer(self, request: ChatRequest) -> ChatResponse:
        alert_response = self._deterministic_alert_response(request)
        if alert_response is not None:
            return alert_response

        context_payload = ContextBuilder.build_context(request.astronaut_id, request.ml_context, [])
        system_prompt = (
            "You are a cautious AI health assistant for a prototype astronaut monitoring system. "
            "Use only the supplied information. Do not invent astronaut data, diagnoses, or NASA citations. "
            "If the data is simulated, clearly identify it as simulated. State uncertainty and limitations. "
            "Never present unsupported medical conclusions as facts."
        )
        prompt = self._compose_prompt(request, context_payload)
        try:
            answer = self.llm_service.generate(prompt, system_prompt=system_prompt)
            summary = answer.strip() or "The system could not produce a helpful answer from the available data."
        except Exception as exc:  # pragma: no cover
            logger.warning("LLM generation failed: %s", exc)
            summary = (
                "The external AI service is unavailable. The system is running in offline mode and is limited to the validated alert and telemetry context."
            )

        return ChatResponse(
            astronaut_id=request.astronaut_id,
            answer=summary,
            evidence=["Validated astronaut data and local evidence only."],
            sources=[],
            status="ok",
            uncertainty="The answer is limited by the available data, safety rules, and prototype constraints.",
            offline_mode=self.llm_service.offline,
            session_id=request.session_id,
        )

    def _deterministic_alert_response(self, request: ChatRequest) -> ChatResponse | None:
        question = self._normalize_question(request.question)
        if not self._is_alert_question(question):
            return None

        record_data = self._resolve_alert_data(request)
        if record_data is None:
            return ChatResponse(
                astronaut_id=request.astronaut_id,
                answer=(
                    f"No ML alert data is available for astronaut {request.astronaut_id}. "
                    "The system cannot explain a missing alert without the underlying telemetry or demo data."
                ),
                evidence=["No available astronaut alert data found."],
                sources=[],
                status="ok",
                uncertainty="No monitoring data was provided for this astronaut, so the alert cannot be interpreted without the source telemetry.",
                offline_mode=True,
                session_id=request.session_id,
            )

        try:
            normalized_record = self._normalize_alert_record(record_data)
            record = MLInputRecord.model_validate(normalized_record)
        except ValueError as exc:
            return ChatResponse(
                astronaut_id=request.astronaut_id,
                answer=(
                    f"The alert data for astronaut {request.astronaut_id} is incomplete or invalid, so it cannot be explained safely. "
                    "Please provide a valid reading with metric, current value, and baseline context."
                ),
                evidence=[str(exc)],
                sources=[],
                status="ok",
                uncertainty="The alert input is incomplete, so the system is not inferring missing medical facts.",
                offline_mode=True,
                session_id=request.session_id,
            )

        explanation = AlertExplainer.explain(record)
        answer = self._format_alert_answer(explanation)
        return ChatResponse(
            astronaut_id=request.astronaut_id,
            answer=answer,
            evidence=[explanation.title, *explanation.observations],
            sources=[item for item in explanation.sources if item] or [str(record.data_source or "simulated")],
            status=explanation.status,
            uncertainty=explanation.uncertainty,
            offline_mode=True,
            session_id=request.session_id,
        )

    def _resolve_alert_data(self, request: ChatRequest) -> dict[str, Any] | None:
        if request.ml_context:
            return request.ml_context

        if request.astronaut_id == "AST-001":
            demo_context = default_context_store.get_default_demo_context()
            if demo_context:
                return demo_context

        if request.astronaut_id:
            demo_context = default_context_store.get(request.astronaut_id)
            if demo_context:
                return demo_context

        return None

    @staticmethod
    def _normalize_alert_record(record_data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(record_data)
        normalized.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        normalized.setdefault("data_source", "simulated")
        normalized.setdefault("sensor_quality", "good")
        normalized.setdefault("trend", "unknown")
        normalized.setdefault("anomaly_detected", False)
        normalized.setdefault("score_definition", "example_score_not_medical_probability")
        normalized.setdefault("model_name", "prototype_offline_model")
        if "metric" not in normalized and normalized.get("current_metric"):
            normalized["metric"] = normalized["current_metric"]
        if "unit" not in normalized and normalized.get("metric") == "heart_rate":
            normalized["unit"] = "bpm"
        if "astronaut_id" not in normalized and normalized.get("id"):
            normalized["astronaut_id"] = normalized["id"]
        return normalized

    @staticmethod
    def _normalize_question(question: str) -> str:
        normalized = question.strip().lower().replace("aegis", "").strip()
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    @staticmethod
    def _is_alert_question(question: str) -> bool:
        alert_keywords = {
            "heart rate alert",
            "heart rate unusual",
            "current heart rate",
            "latest health alert",
            "explain my heart rate alert",
            "why is my heart rate unusual",
            "what is my current heart rate",
            "explain my latest health alert",
        }
        return any(keyword in question for keyword in alert_keywords)

    @staticmethod
    def _format_alert_answer(explanation: Any) -> str:
        base = (
            f"The current heart rate is {explanation.observations[0].split(': ', 1)[1] if len(explanation.observations) > 0 and ': ' in explanation.observations[0] else 'unavailable'}. "
            f"The astronaut's personal baseline is {explanation.observations[1].split(': ', 1)[1] if len(explanation.observations) > 1 and ': ' in explanation.observations[1] else 'unavailable'}. "
            f"{explanation.explanation} "
            f"{explanation.uncertainty}"
        )
        return base

    @staticmethod
    def _compose_prompt(request: ChatRequest, context: dict[str, Any]) -> str:
        ml = request.ml_context or {}
        return (
            f"Question: {request.question}\n"
            f"Astronaut ID: {request.astronaut_id}\n"
            f"Current context: {context}\n"
            f"Validated ML context: {ml}\n"
            "Answer using only the supplied evidence. If there is no sufficient evidence, say so. "
            "Do not invent diagnoses, measurements, or NASA citations."
        )
