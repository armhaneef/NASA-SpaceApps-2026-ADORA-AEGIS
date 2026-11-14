from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_route():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_vite_origin_is_explicitly_allowed_for_chat_ui():
    response = client.options(
        "/api/v1/chat",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_demo_route():
    response = client.get("/api/v1/demo")
    assert response.status_code == 200
    assert response.json()["astronaut_id"] == "AST-001"


def test_explain_route():
    payload = {
        "astronaut_id": "AST-001",
        "timestamp": "2026-11-14T07:00:00Z",
        "metric": "heart_rate",
        "current_value": 110,
        "baseline_value": 72,
        "unit": "bpm",
        "anomaly_detected": True,
        "anomaly_score": 0.87,
        "score_definition": "example_score_not_medical_probability",
        "trend": "increasing",
        "sensor_quality": "good",
        "data_source": "simulated",
        "model_name": "isolation_forest",
        "context": {"activity": "unknown"},
    }
    response = client.post("/api/v1/alerts/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["astronaut_id"] == "AST-001"
    assert data["status"] == "review"


def test_chat_route():
    payload = {
        "astronaut_id": "AST-001",
        "question": "Why was my heart rate flagged?",
        "include_context": True,
        "ml_context": {
            "metric": "heart_rate",
            "current_value": 110,
            "baseline_value": 72,
            "anomaly_detected": True,
            "trend": "increasing",
        },
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    assert "answer" in response.json()


def test_chat_reports_real_provider_success_as_online(monkeypatch):
    class SuccessfulProvider:
        offline = False

        def generate(self, prompt, *, system_prompt=None, temperature=0.2):
            assert "Question: Explain the sleep schedule." in prompt
            return "Model-generated response for this test."

    monkeypatch.setattr("app.api.routes.LLMService", SuccessfulProvider)
    response = client.post("/api/v1/chat", json={
        "astronaut_id": "AST-SYNTHETIC-01",
        "question": "Explain the sleep schedule.",
    })

    assert response.status_code == 200
    assert response.json()["answer"] == "Model-generated response for this test."
    assert response.json()["offline_mode"] is False


def test_chat_marks_provider_failure_fallback_as_offline(monkeypatch):
    class FailingProvider:
        offline = False

        def generate(self, prompt, *, system_prompt=None, temperature=0.2):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr("app.api.routes.LLMService", FailingProvider)
    response = client.post("/api/v1/chat", json={
        "astronaut_id": "AST-SYNTHETIC-01",
        "question": "Explain the sleep schedule.",
    })

    assert response.status_code == 200
    assert response.json()["offline_mode"] is True
    assert "offline mode" in response.json()["answer"].lower()


def test_voice_demo_route():
    response = client.get("/api/v1/voice-demo")
    assert response.status_code == 200
    assert "ADORA AEGIS Voice Assistant Demo" in response.text


def test_voice_status_route():
    response = client.get("/api/v1/voice/status")
    assert response.status_code == 200
    data = response.json()
    assert "microphone_available" in data
    assert "speech_output_available" in data
