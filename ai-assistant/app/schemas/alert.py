from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SUPPORTED_METRICS: dict[str, set[str]] = {
    "heart_rate": {"bpm"},
    "spO2": {"%"},
    "sleep_duration": {"hours"},
    "respiration_rate": {"breaths/min"},
    "temperature": {"C", "F"},
    "body_temperature": {"C", "F"},
    "ecg_hr": {"bpm"},
    "stress_index": {"au"},
    "co2": {"ppm"},
    "humidity": {"%"},
    "radiation": {"mSv"},
}

TrendLiteral = Literal["increasing", "decreasing", "stable", "unknown"]
QualityLiteral = Literal["good", "fair", "poor", "unknown"]


class MLInputRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    astronaut_id: str = Field(..., min_length=1)
    timestamp: str | datetime
    metric: str
    current_value: float | None = None
    baseline_value: float | None = None
    unit: str
    anomaly_detected: bool = False
    anomaly_score: float | None = None
    score_definition: str | None = None
    trend: TrendLiteral | str = "unknown"
    sensor_quality: QualityLiteral | str = "unknown"
    data_source: str = "simulated"
    model_name: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("astronaut_id")
    @classmethod
    def validate_astronaut_id(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("astronaut_id is required")
        return value.strip()

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str | datetime) -> str | datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value
        text = value.strip()
        if not text:
            raise ValueError("timestamp is required")
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be ISO-8601 with timezone information") from exc
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    @field_validator("metric")
    @classmethod
    def validate_metric(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("metric is required")
        cleaned = value.strip()
        if cleaned not in SUPPORTED_METRICS:
            raise ValueError(f"Unsupported metric '{cleaned}'. Supported metrics: {sorted(SUPPORTED_METRICS)}")
        return cleaned

    @model_validator(mode="after")
    def validate_metric_unit_pair(self) -> "MLInputRecord":
        allowed_units = SUPPORTED_METRICS[self.metric]
        if self.unit not in allowed_units:
            raise ValueError(f"Unsupported unit '{self.unit}' for metric '{self.metric}'. Allowed units: {sorted(allowed_units)}")
        if self.current_value is not None and not isinstance(self.current_value, (int, float)):
            raise ValueError("current_value must be numeric when provided")
        if self.baseline_value is not None and not isinstance(self.baseline_value, (int, float)):
            raise ValueError("baseline_value must be numeric when provided")
        if self.anomaly_score is not None and not isinstance(self.anomaly_score, (int, float)):
            raise ValueError("anomaly_score must be numeric when provided")
        if self.sensor_quality not in {"good", "fair", "poor", "unknown"}:
            raise ValueError("sensor_quality must be one of: good, fair, poor, unknown")
        if self.trend not in {"increasing", "decreasing", "stable", "unknown"}:
            raise ValueError("trend must be one of: increasing, decreasing, stable, unknown")
        return self

    @property
    def has_baseline(self) -> bool:
        return self.baseline_value is not None

    @property
    def delta_from_baseline(self) -> float | None:
        if self.current_value is None or self.baseline_value is None:
            return None
        return float(self.current_value - self.baseline_value)

    @property
    def baseline_status(self) -> str:
        if self.baseline_value is None:
            return "missing baseline"
        if self.current_value is None:
            return "missing current reading"
        if self.current_value > self.baseline_value:
            return "above baseline"
        if self.current_value < self.baseline_value:
            return "below baseline"
        return "at baseline"


class SupportedMetric(BaseModel):
    metric: str
    allowed_units: list[str]
    notes: str = "Illustrative prototype metric, not medically validated."
