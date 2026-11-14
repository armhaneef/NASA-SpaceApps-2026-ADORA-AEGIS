"""Minimal FastAPI entry point for the ADORA-AEGIS backend."""

from fastapi import FastAPI

from app.routes.health import router as health_router

app = FastAPI(
    title="ADORA-AEGIS API",
    description="Starter API for a synthetic astronaut health-monitoring prototype.",
    version="0.1.0",
)


app.include_router(health_router)
