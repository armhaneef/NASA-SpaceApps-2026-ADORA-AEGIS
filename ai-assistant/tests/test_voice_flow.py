from fastapi.testclient import TestClient

from app.api.routes import create_app


client = TestClient(create_app())


def test_voice_question_uses_alert_explainer_for_heart_rate_alert():
    payload = {
        "astronaut_id": "AST-001",
        "question": "AEGIS, explain my heart rate alert.",
        "include_context": True,
        "ml_context": {
            "astronaut_id": "AST-001",
            "metric": "heart_rate",
            "current_value": 110,
            "baseline_value": 72,
            "unit": "bpm",
            "anomaly_detected": True,
            "trend": "increasing",
            "sensor_quality": "good",
            "data_source": "simulated",
        },
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "110" in body["answer"]
    assert "72" in body["answer"]
    assert "baseline" in body["answer"].lower()
    assert "offline demonstration mode" not in body["answer"].lower()


def test_voice_question_without_ml_data_returns_clear_unavailable_message():
    payload = {
        "astronaut_id": "AST-002",
        "question": "Explain my latest health alert.",
        "include_context": True,
        "ml_context": None,
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "no ml alert data" in body["answer"].lower()
