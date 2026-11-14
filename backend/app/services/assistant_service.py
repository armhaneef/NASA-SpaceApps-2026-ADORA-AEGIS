"""Select minimal astronaut-scoped context without storing conversations."""

from sqlalchemy.orm import Session

from app.schemas.assistant import AnalysisContext, AssistantContext
from app.schemas.assistant import AssistantProviderRequest, AssistantRequest, AssistantResponse
from app.services.analysis_service import get_analysis
from app.services.astronaut_service import get_astronaut
from app.services.ai_adapter import AIAdapter


def ask_assistant(session: Session, request: AssistantRequest, adapter: AIAdapter) -> AssistantResponse:
    get_astronaut(session, request.astronaut_id)
    context = AssistantContext()
    if request.analysis_id is not None:
        analysis = get_analysis(session, request.astronaut_id, request.analysis_id)
        raw = analysis.ml_result
        context.analysis = AnalysisContext(
            analysis_id=analysis.id, analysis_timestamp=analysis.analysis_timestamp,
            measurement_timestamp=analysis.measurement_timestamp, status=analysis.status,
            is_mock=analysis.is_mock, anomaly_detected=analysis.anomaly_detected,
            anomaly_score=analysis.anomaly_score, affected_measurements=analysis.affected_measurements,
            model_version=analysis.model_version, data_source=analysis.data_source,
            data_quality=raw["data_quality"] if raw is not None else None,
            detector_method=raw["anomaly"]["method"] if raw is not None else None,
            sensor_method=raw["anomaly"]["sensor_method"] if raw is not None else None,
        )
    payload = AssistantProviderRequest(
        astronaut_id=request.astronaut_id, question=request.question, context=context
    )
    return adapter.respond(payload, request.mode)
