from app.services.llm_service import LLMService


def test_offline_service_handles_questions():
    service = LLMService(provider="offline")
    answer = service.generate("Why was my heart rate flagged?")
    assert "offline" in answer.lower()
    assert "structured" in answer.lower() or "deterministic" in answer.lower()


def test_invalid_provider_raises_error():
    service = LLMService(provider="unsupported")
    service.offline = False
    try:
        service.generate("test")
        assert False, "Expected a provider validation failure"
    except RuntimeError:
        pass
