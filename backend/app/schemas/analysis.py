"""Backend analysis envelope; full Member 2 output remains nested unchanged."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictBool

from app.schemas.astronaut import Identifier
from app.schemas.sensor import Source, Timestamp


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["mock", "local"] = "mock"
    source: Source
    timestamp: Timestamp | None = None
    history_limit: int = Field(default=100, ge=0, le=200)
    temperature_is_skin: StrictBool = False


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    astronaut_id: Identifier
    analysis_timestamp: Timestamp
    measurement_timestamp: Timestamp
    status: Literal["mock", "normal", "anomaly", "insufficient_data"]
    is_mock: bool
    anomaly_detected: bool | None
    anomaly_score: float | None
    affected_measurements: list[str]
    explanations: list[str]
    model_version: str
    data_source: str
    prepared_input: dict[str, JsonValue]
    input_readings: list[dict[str, JsonValue]]
    ml_result: dict[str, JsonValue] | None
    preparation_notes: list[str] = Field(default_factory=list)


class AnalysisRead(AnalysisResult):
    id: int
