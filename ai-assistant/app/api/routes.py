from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.knowledge_store import KnowledgeStore
from app.schemas.backend_integration import BackendAssistantRequest, BackendAssistantResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.response import AlertExplanationResponse, HealthResponse, KnowledgeSearchResponse
from app.services.alert_explainer import AlertExplainer
from app.services.backend_integration import respond_to_backend
from app.services.health_assistant import HealthAssistant
from app.services.llm_service import LLMCallError, LLMService
from app.services.voice_service import VoiceService
from app.safety.input_guard import InputGuard
from app.safety.medical_policy import MedicalPolicy
from app.safety.output_guard import OutputGuard

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1")
knowledge_store = KnowledgeStore()


@router.get("/health", response_model=HealthResponse)
def ai_health() -> HealthResponse:
    llm_available = LLMService().is_available()
    return HealthResponse(
        status="ok",
        service="ai-assistant",
        mode="configured" if llm_available else "offline",
        metadata={
            "llm_provider": settings.llm_provider,
            "llm_available": llm_available,
            "knowledge_documents": len(knowledge_store.documents),
        },
    )


@router.get("/demo")
def demo() -> dict[str, Any]:
    return {
        "astronaut_id": "AST-001",
        "scenario": "simulated heart-rate anomaly",
        "alert": {
            "title": "Unusual Heart Rate Pattern",
            "status": "review",
            "explanation": "The simulated heart rate reading is above the astronaut's personal baseline. The available information does not establish the cause.",
            "data_source": "simulated",
            "medical_diagnosis": False,
        },
    }


@router.post("/alerts/explain", response_model=AlertExplanationResponse)
def explain_alert(payload: dict[str, Any]) -> AlertExplanationResponse:
    try:
        record = InputGuard.validate_ml_record(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return AlertExplainer.explain(record)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: dict[str, Any]) -> ChatResponse:
    try:
        request = ChatRequest.model_validate(payload)
        InputGuard.validate_question(request.question)
        MedicalPolicy.ensure_supported_request(request.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    assistant = HealthAssistant(llm_service=LLMService())
    response = assistant.answer(request)
    validated = OutputGuard.validate_response(response.model_dump())
    return ChatResponse.model_validate(validated)


@router.post("/assistant/respond", response_model=BackendAssistantResponse)
def backend_assistant(payload: BackendAssistantRequest) -> BackendAssistantResponse:
    try:
        response = respond_to_backend(payload.model_dump(mode="json"))
        return BackendAssistantResponse.model_validate(response)
    except LLMCallError as exc:
        logger.warning("Backend assistant provider unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Configured local assistant provider is unavailable.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
def knowledge_search(payload: dict[str, Any]) -> KnowledgeSearchResponse:
    query = str(payload.get("query", "")).strip()
    if not query:
        raise HTTPException(status_code=400, detail="A search query is required.")
    results = knowledge_store.search(query, limit=int(payload.get("limit", 5)))
    return KnowledgeSearchResponse(
        query=query,
        results=results,
        evidence_available=bool(results),
        message="Knowledge base evidence available." if results else "The knowledge base does not contain enough relevant evidence for this query.",
    )


@router.get("/knowledge/status", response_model=dict[str, Any])
def knowledge_status() -> dict[str, Any]:
    return knowledge_store.status()


@router.get("/voice-demo")
def voice_demo() -> FileResponse:
    file_path = Path(__file__).resolve().parents[1] / "static" / "voice_demo.html"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Voice demo page not found.")
    return FileResponse(file_path)


@router.get("/voice/status")
def voice_status() -> dict[str, Any]:
    return VoiceService.status()


@router.post("/voice/transcribe")
def voice_transcribe(payload: dict[str, Any]) -> dict[str, Any]:
    duration = float(payload.get("duration", 5.0) or 5.0)
    try:
        transcript = VoiceService().listen_once(duration=duration)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"transcript": transcript, "status": "ok"}


@router.post("/voice/speak")
def voice_speak(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text", "") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="A text value is required for spoken output.")
    try:
        VoiceService().speak(text)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ok", "message": "Spoken output queued."}


def create_app() -> Any:
    from fastapi import FastAPI

    app = FastAPI(
        title="ADORA AEGIS AI Assistant",
        version="0.1.0",
        description="Prototype AI member for astronaut health explanation and local knowledge retrieval.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        # The API uses JSON requests, not cookie/session authentication.
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app
