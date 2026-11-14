"""Minimal FastAPI entry point for the ADORA-AEGIS backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.database.connection import init_db

from app.routes.health import router as health_router
from app.routes.astronauts import router as astronauts_router
from app.routes.sensors import router as sensors_router
from app.services.errors import ConflictError, NotFoundError
from app.services.errors import MLResponseError, MLUnavailableError
from app.routes.analyses import router as analyses_router
from app.routes.assistant import router as assistant_router
from app.services.errors import AssistantResponseError, AssistantTimeoutError, AssistantUnavailableError

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize local storage once when the application starts."""
    init_db()
    yield


app = FastAPI(
    title="ADORA-AEGIS API",
    description="Starter API for a synthetic astronaut health-monitoring prototype.",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(health_router)
app.include_router(astronauts_router)
app.include_router(sensors_router)
app.include_router(analyses_router)
app.include_router(assistant_router)


@app.exception_handler(AssistantUnavailableError)
async def assistant_unavailable(request: Request, exc: AssistantUnavailableError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(AssistantResponseError)
async def assistant_invalid_response(request: Request, exc: AssistantResponseError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(AssistantTimeoutError)
async def assistant_timeout(request: Request, exc: AssistantTimeoutError):
    return JSONResponse(status_code=504, content={"detail": str(exc)})


@app.exception_handler(MLUnavailableError)
async def ml_unavailable(request: Request, exc: MLUnavailableError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(MLResponseError)
async def ml_invalid_response(request: Request, exc: MLResponseError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(NotFoundError)
async def not_found(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, exc: RequestValidationError):
    # Keep errors JSON-safe (even for NaN/Infinity) without echoing profile data.
    errors = [{key: error[key] for key in ("type", "loc", "msg")}
              for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})
