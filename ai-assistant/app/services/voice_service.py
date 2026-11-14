from __future__ import annotations

from typing import Any


class VoiceService:
    """Optional voice input/output support for local demo scenarios."""

    @staticmethod
    def status() -> dict[str, Any]:
        microphone_available = False
        speech_output_available = False

        try:
            import speech_recognition as sr  # type: ignore

            microphone_available = bool(sr.Microphone.list_microphone_names())
        except Exception:
            microphone_available = False

        try:
            import pyttsx3  # type: ignore

            speech_output_available = pyttsx3.init() is not None
        except Exception:
            speech_output_available = False

        if microphone_available and speech_output_available:
            mode = "full"
        elif microphone_available or speech_output_available:
            mode = "partial"
        else:
            mode = "offline"

        return {
            "microphone_available": microphone_available,
            "speech_output_available": speech_output_available,
            "mode": mode,
        }

    def listen_once(self, duration: float = 5.0) -> str:
        try:
            import speech_recognition as sr  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Voice input requires the optional SpeechRecognition dependency.") from exc

        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=duration)
            transcript = recognizer.recognize_google(audio)
            return transcript.strip()
        except sr.WaitTimeoutError as exc:
            raise RuntimeError("No speech was detected within the listening window.") from exc
        except sr.UnknownValueError as exc:
            raise RuntimeError("Speech was detected, but it could not be understood.") from exc
        except sr.RequestError as exc:
            raise RuntimeError(f"Speech recognition service is unavailable: {exc}") from exc

    def speak(self, text: str) -> bool:
        cleaned = str(text or "").strip()
        if not cleaned:
            raise ValueError("Text for spoken output is required.")

        try:
            import pyttsx3  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Speech output requires the optional pyttsx3 dependency.") from exc

        engine = pyttsx3.init()
        engine.say(cleaned)
        engine.runAndWait()
        return True
