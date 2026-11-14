"""Draft assistant boundary; no provider-specific prompts or medical logic."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictBool, StringConstraints

from app.schemas.astronaut import Identifier
from app.schemas.sensor import Timestamp

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Answer = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=12000)]
Version = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Limitation = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class AssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    astronaut_id: Identifier
    question: Question
    mode: Literal["mock", "local"] = "mock"
    analysis_id: Annotated[int, Field(strict=True, ge=1)] | None = None


class AnalysisContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: int
    analysis_timestamp: Timestamp
    measurement_timestamp: Timestamp
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


class AssistantContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis: AnalysisContext | None = None


class AssistantProviderRequest(BaseModel):
    """Only these fields are forwarded to the approved local provider."""

    model_config = ConfigDict(extra="forbid")
    astronaut_id: Identifier
    question: Question
    context: AssistantContext


class AssistantProviderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    astronaut_id: Identifier
    answer: Answer
    assistant_version: Version
    is_mock: StrictBool
    limitations: Annotated[list[Limitation], Field(min_length=1, max_length=20)]


class AssistantResponse(AssistantProviderResponse):
    response_timestamp: Timestamp
    mode: Literal["mock", "local"]
    status: Literal["mock", "completed"]
    data_source: Literal["backend_mock", "configured_local_provider"]
    context: AssistantContext
