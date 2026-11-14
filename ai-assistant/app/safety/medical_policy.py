from __future__ import annotations


class MedicalPolicy:
    """Boundaries for a prototype, non-diagnostic AI system."""

    @staticmethod
    def ensure_supported_request(question: str) -> None:
        lowered = question.lower()
        if any(term in lowered for term in ["diagnose", "treat", "prescribe"]):
            raise ValueError("This prototype does not provide medical diagnoses or treatment decisions. Please use approved mission protocols and qualified medical personnel.")

    @staticmethod
    def safe_recommendation() -> str:
        return "Consult approved mission procedures and qualified medical personnel for clinical concerns."
