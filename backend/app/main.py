"""Minimal FastAPI entry point for the ADORA-AEGIS backend."""

from fastapi import FastAPI

app = FastAPI(
    title="ADORA-AEGIS API",
    description="Starter API for a synthetic astronaut health-monitoring prototype.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report that the API process is responding."""
    return {"status": "ok"}
