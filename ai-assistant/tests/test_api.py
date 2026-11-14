from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_route():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


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
