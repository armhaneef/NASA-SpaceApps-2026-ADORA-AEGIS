import sys
from types import ModuleType, SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routes import create_app
from app.services.voice_service import VoiceService


client = TestClient(create_app())


def test_voice_service_status_reports_capabilities():
    status = VoiceService.status()
    assert "microphone_available" in status
    assert "speech_output_available" in status
    assert status["mode"] in {"offline", "partial", "full"}


def test_listen_once_uses_recognizer_and_returns_transcript(monkeypatch):
    calls = []

    class FakeMicrophone:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeRecognizer:
        def adjust_for_ambient_noise(self, _source, duration):
            calls.append(("calibrate", duration))

        def listen(self, _source, timeout):
            calls.append(("listen", timeout))
            return "audio"

        def recognize_google(self, audio):
            calls.append(("recognize", audio))
            return "  Explain the simulated alert.  "

    fake_module = ModuleType("speech_recognition")
    fake_module.Recognizer = FakeRecognizer
    fake_module.Microphone = FakeMicrophone
    monkeypatch.setitem(sys.modules, "speech_recognition", fake_module)

    transcript = VoiceService().listen_once(duration=3.0)

    assert transcript == "Explain the simulated alert."
    assert calls == [("calibrate", 0.5), ("listen", 3.0), ("recognize", "audio")]


def test_speak_sends_text_to_tts_engine(monkeypatch):
    calls = []
    engine = SimpleNamespace(
        say=lambda text: calls.append(("say", text)),
        runAndWait=lambda: calls.append(("run", None)),
    )
    fake_module = ModuleType("pyttsx3")
    fake_module.init = lambda: engine
    monkeypatch.setitem(sys.modules, "pyttsx3", fake_module)

    assert VoiceService().speak("  Simulated response.  ") is True
    assert calls == [("say", "Simulated response."), ("run", None)]


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
