from fastapi.testclient import TestClient

from app.api.routes import create_app
from app.services.voice_service import VoiceService


client = TestClient(create_app())


def test_voice_service_status_reports_capabilities():
    status = VoiceService.status()
    assert "microphone_available" in status
    assert "speech_output_available" in status
    assert status["mode"] in {"offline", "partial", "full"}


def test_voice_api_routes_handle_mocked_audio(monkeypatch):
    def fake_listen_once(self, duration=5.0):
        return "Why was my heart rate flagged?"

    def fake_speak(self, text: str):
        return True

    monkeypatch.setattr(VoiceService, "listen_once", fake_listen_once)
    monkeypatch.setattr(VoiceService, "speak", fake_speak)

    response = client.post("/api/v1/voice/transcribe", json={"duration": 5.0})
    assert response.status_code == 200
    assert response.json()["transcript"] == "Why was my heart rate flagged?"

    speak_response = client.post("/api/v1/voice/speak", json={"text": "Review the alert context."})
    assert speak_response.status_code == 200
    assert speak_response.json()["status"] == "ok"
