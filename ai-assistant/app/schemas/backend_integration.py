from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictBool, StringConstraints

Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Answer = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=12000)]
Version = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Limitation = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class BackendAnalysisSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: int = Field(ge=1)
    analysis_timestamp: str
    measurement_timestamp: str
    status: Literal["mock", "normal", "anomaly", "insufficient_data"]
    is_mock: StrictBool
    anomaly_detected: StrictBool | None
    anomaly_score: float | None
    affected_measurements: list[str]
    model_version: str
    data_source: str
    data_quality: dict[str, JsonValue] | None
    detector_method: str | None
    sensor_method: str | None


class BackendAssistantContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis: BackendAnalysisSummary | None


class BackendAssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    astronaut_id: Identifier
    question: Question
    context: BackendAssistantContext


class BackendAssistantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    astronaut_id: Identifier
    answer: Answer
    assistant_version: Version
    is_mock: StrictBool
    limitations: Annotated[list[Limitation], Field(min_length=1, max_length=20)]
