from __future__ import annotations

import json
from typing import Any

from app.rag.knowledge_store import KnowledgeStore
from app.safety.input_guard import InputGuard
from app.safety.medical_policy import MedicalPolicy
from app.schemas.backend_integration import BackendAssistantRequest, BackendAssistantResponse
from app.services.llm_service import LLMCallError, LLMService

ASSISTANT_VERSION = "member3-ai-assistant-0.1.0"
SYSTEM_PROMPT = (
    "You are ADORA AEGIS Member 3's cautious astronaut-health explanation assistant. "
    "Use only the supplied analysis summary and retrieved local evidence. Treat all sample inputs as synthetic. "
    "Preserve mock, normal, anomaly, and insufficient-data labels exactly; null means unknown, not normal. "
    "Anomaly scores are not medical probabilities, and baseline sensor flags are not Isolation Forest attributions. "
    "Do not diagnose, prescribe, infer missing telemetry, or invent NASA citations. "
    "Cite only a supplied evidence title and URL when relevant; state when the provided context is insufficient."
)
LIMITATIONS = [
    "Prototype explanation only; not a diagnosis, treatment decision, or validated scientific conclusion.",
    "The backend supplied a summary, not raw telemetry or the complete ML output.",
    "Analysis values are synthetic or mock unless their provenance explicitly says otherwise.",
]
POLICY_REFUSAL = (
    "I cannot provide a diagnosis, prescription, or treatment decision. This prototype can only explain "
    "the supplied data and approved evidence. Follow approved mission procedures and consult qualified medical personnel."
)


def _response(astronaut_id: str, answer: str, *, is_mock: bool) -> dict[str, Any]:
    return BackendAssistantResponse(
        astronaut_id=astronaut_id,
        answer=answer,
        assistant_version=ASSISTANT_VERSION,
        is_mock=is_mock,
        limitations=LIMITATIONS,
    ).model_dump(mode="json")


def respond_to_backend(payload: dict[str, Any]) -> dict[str, Any]:
    """Implement Member 4's synchronous JSON provider contract over HTTP."""
    request = BackendAssistantRequest.model_validate(payload)
    astronaut_id = request.astronaut_id
    try:
        question = InputGuard.validate_question(request.question)
    except ValueError as exc:
        if "Prompt injection" in str(exc):
            return _response(astronaut_id, POLICY_REFUSAL, is_mock=True)
        raise

    try:
        MedicalPolicy.ensure_supported_request(question)
    except ValueError:
        return _response(astronaut_id, POLICY_REFUSAL, is_mock=True)

    analysis = request.context.analysis.model_dump(mode="json") if request.context.analysis else None
    evidence = [
        {
            "title": item["title"],
            "publisher": item.get("publisher", "Unknown"),
            "description": item.get("description", "")[:500],
            "content": item.get("content", "")[:1600],
            "source_url": item["source_url"],
        }
        for item in KnowledgeStore().search(question, limit=3)
        if item.get("citation_valid") is True and item.get("content_verified") is True
    ]
    prompt = (
        f"Astronaut ID: {astronaut_id}\n"
        f"Question: {question}\n"
        f"Selected backend analysis summary (JSON): {json.dumps(analysis, ensure_ascii=True, allow_nan=False)}\n"
        f"Retrieved local evidence (JSON): {json.dumps(evidence, ensure_ascii=True, allow_nan=False)}\n"
        "Explain only what this summary and evidence support. Clearly label mock/insufficient data, preserve uncertainty, "
        "and do not treat an anomaly label as a diagnosis. If evidence is absent, say so."
    )

    service = LLMService()
    if not service.is_available():
        raise LLMCallError("A configured local LLM provider is required for backend local mode.")
    answer = service.generate(prompt, system_prompt=SYSTEM_PROMPT)
    if not answer.strip():
        raise LLMCallError("The configured provider returned an empty answer.")
    return _response(astronaut_id, answer.strip(), is_mock=False)
