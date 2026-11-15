"""Sensor ingestion, latest readings, and chart history endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database.connection import get_session
from app.schemas.sensor import GroupedReading, MEASUREMENTS, SensorCreate, SensorRead, Timestamp
from app.services import sensor_service as service

router = APIRouter(prefix="/health", tags=["sensor readings"])
Database = Annotated[Session, Depends(get_session)]


def measurement_filter(measurement_type: str | None = None) -> str | None:
    if measurement_type is not None and measurement_type not in MEASUREMENTS:
        raise HTTPException(422, "Unsupported measurement_type")
    return measurement_type


@router.post("/ingest", response_model=list[SensorRead])
def ingest(payload: SensorCreate | GroupedReading, session: Database, response: Response):
    readings = payload.to_readings() if isinstance(payload, GroupedReading) else [payload]
    records, created = service.ingest(session, readings)
    response.status_code = 201 if created else 200
    return records


@router.get("/{astronaut_id}/latest", response_model=list[SensorRead])
def latest(astronaut_id: str, session: Database,
           measurement_type: Annotated[str | None, Depends(measurement_filter)]):
    """Newest reading per measurement type; ID breaks timestamp ties."""
    return service.latest(session, astronaut_id, measurement_type)


@router.get("/{astronaut_id}/history", response_model=list[SensorRead])
def history(astronaut_id: str, session: Database,
            measurement_type: Annotated[str | None, Depends(measurement_filter)],
            start: Annotated[Timestamp | None, Query()] = None,
            end: Annotated[Timestamp | None, Query()] = None,
            limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    """Chronological history with inclusive time bounds and pagination."""
    if start is not None and end is not None and start > end:
        raise HTTPException(422, "start must be earlier than or equal to end")
    return service.history(session, astronaut_id, measurement_type, start, end, limit, offset)
