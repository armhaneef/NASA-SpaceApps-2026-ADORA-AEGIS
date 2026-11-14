"""Standalone integration example; it does not import or modify backend/app."""

from typing import Annotated

from fastapi import Body, FastAPI

from aegis_ml import analyze_health

app = FastAPI(
    title="AEGIS ML integration example",
    description="Synthetic-data prototype; no clinical validation.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ml/analyze", tags=["ml"])
def analyze(payload: Annotated[dict, Body()]) -> dict:
    """Return the ML result unchanged, including quality errors and nulls.

    This synchronous route lets FastAPI run model work in its worker thread pool.
    The demo accepts history in the body; a real backend should attach history
    from its astronaut-specific synthetic data store before calling the function.
    """
    return analyze_health(payload)
