"""Astronaut API schemas."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator
from pydantic import StringConstraints

Identifier = Annotated[str, StringConstraints(
    strip_whitespace=True, min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"
)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Role = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class AstronautCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    astronaut_id: Identifier
    name: Name
    mission_id: Identifier
    mission_role: Role
    profile_metadata: dict[str, JsonValue] = Field(default_factory=dict)


class AstronautUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    name: Name | None = None
    mission_id: Identifier | None = None
    mission_role: Role | None = None
    profile_metadata: dict[str, JsonValue] | None = None

    @model_validator(mode="after")
    def require_changes(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one profile field")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Profile fields cannot be null")
        return self


class AstronautRead(AstronautCreate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    created_at: datetime
