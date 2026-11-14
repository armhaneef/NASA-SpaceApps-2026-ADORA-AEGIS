from __future__ import annotations

from app.schemas.alert import MLInputRecord
from app.schemas.response import AlertExplanationResponse


class AlertExplainer:
    """Create deterministic explanations for validated ML outputs."""

    @staticmethod
    def explain(record: MLInputRecord) -> AlertExplanationResponse:
        metric_label = record.metric.replace("_", " ").replace("spO2", "SpO₂")
        if record.current_value is None:
            observations = ["No current value was provided for this metric."]
            explanation = "The available monitoring data does not include a current reading for this metric. The cause cannot be determined from the provided information alone."
            title = f"Missing {metric_label} Reading"
            status = "review"
            suggested_next_step = "Review the sensor input, confirm the data stream, and check whether the reading was missing or delayed."
            uncertainty = "The cause cannot be determined without the current measurement."
        else:
            if record.baseline_value is None:
                observations = [f"Current {metric_label}: {record.current_value} {record.unit}"]
                explanation = "The current reading is available, but no personal baseline was supplied for comparison. The available information does not establish the cause."
                title = f"{metric_label.title()} Reading Needs Context"
                status = "review"
                suggested_next_step = "Review recent activity, sensor quality, and the astronaut's personal baseline if it becomes available."
                uncertainty = "A baseline comparison is unavailable, so the interpretation remains limited."
            else:
                delta = record.current_value - record.baseline_value
                direction = "above" if delta > 0 else "below" if delta < 0 else "at"
                trend_text = record.trend if record.trend != "unknown" else "trend unavailable"
                observations = [
                    f"Current {metric_label}: {record.current_value} {record.unit}",
                    f"Personal baseline: {record.baseline_value} {record.unit}",
                    f"Trend: {trend_text}",
                ]
                if record.anomaly_detected:
                    title = f"Unusual {metric_label.title()} Pattern"
                    explanation = (
                        f"The simulated {metric_label} reading is {direction} the astronaut's personal baseline. "
                        "The available information does not establish the cause."
                    )
                    status = "review"
                    suggested_next_step = "Review recent activity, sensor reliability, and monitoring trends before drawing any conclusion."
                    uncertainty = "The cause cannot be determined from these measurements alone."
                else:
                    title = f"{metric_label.title()} Within Expected Range"
                    explanation = "The current reading is near the provided baseline, and no anomaly was flagged in the prototype ML result. The available information does not establish a diagnosis."
                    status = "ok"
                    suggested_next_step = "Continue routine monitoring and check whether the baseline or context needs to be updated."
                    uncertainty = "The result is limited to the provided baseline and prototype model output."

        if record.sensor_quality == "poor":
            explanation += " Sensor quality is reported as poor, so observed values should be interpreted cautiously."
            uncertainty = "Sensor quality is poor; the reading may be less reliable."

        return AlertExplanationResponse(
            astronaut_id=record.astronaut_id,
            status=status,
            title=title,
            explanation=explanation,
            observations=observations,
            suggested_next_step=suggested_next_step,
            uncertainty=uncertainty,
            sources=[],
            data_source=record.data_source,
            medical_diagnosis=False,
        )
