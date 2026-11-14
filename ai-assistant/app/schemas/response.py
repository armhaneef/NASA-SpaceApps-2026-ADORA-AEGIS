from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "ok"
    service: str = "ai-assistant"
    mode: str = "offline"
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertExplanationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    astronaut_id: str
    status: str
    title: str
    explanation: str
    observations: list[str]
    suggested_next_step: str
    uncertainty: str
    sources: list[str] = Field(default_factory=list)
    data_source: str = "simulated"
    medical_diagnosis: bool = False


class APIErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detail: str
    code: str = "validation_error"


class ChatResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    evidence: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    status: str = "ok"
    uncertainty: str = "The answer is limited by available data and approved evidence."
    offline_mode: bool = True


class KnowledgeSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    results: list[dict[str, Any]] = Field(default_factory=list)
    evidence_available: bool
    message: str
