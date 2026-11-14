from __future__ import annotations

from typing import Any


class ContextBuilder:
    """Create compact astronaut context for the assistant and the RAG layer."""

    @staticmethod
    def build_context(astronaut_id: str, ml_data: dict[str, Any] | None = None, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {
            "astronaut_id": astronaut_id,
            "simulated_data": True,
            "current_metric": None,
            "baseline_value": None,
            "current_value": None,
            "anomaly_detected": False,
            "trend": "unknown",
        }

        if ml_data:
            context["current_metric"] = ml_data.get("metric")
            context["current_value"] = ml_data.get("current_value")
            context["baseline_value"] = ml_data.get("baseline_value")
            context["anomaly_detected"] = bool(ml_data.get("anomaly_detected"))
            context["trend"] = ml_data.get("trend", "unknown")
            context["data_source"] = ml_data.get("data_source", "simulated")
            context["sensor_quality"] = ml_data.get("sensor_quality", "unknown")

        if history:
            context["recent_turns"] = history[-5:]

        return context
