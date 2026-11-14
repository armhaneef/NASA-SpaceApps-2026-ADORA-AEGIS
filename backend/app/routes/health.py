"""Service availability endpoint; this does not assess astronaut health."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Stable response defined by the shared API contract."""

    status: Literal["ok"] = "ok"


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Report that the API process is responding."""
    return HealthResponse()
