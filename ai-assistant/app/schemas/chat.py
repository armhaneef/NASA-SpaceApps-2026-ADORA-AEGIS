from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1, max_length=6000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    astronaut_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None
    include_context: bool = True
    conversation_history: list[ChatTurn] = Field(default_factory=list)
    ml_context: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    astronaut_id: str
    answer: str
    evidence: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    status: str = "ok"
    uncertainty: str = "The answer is limited by the available data and the prototype safety rules."
    offline_mode: bool = True
    session_id: str | None = None
