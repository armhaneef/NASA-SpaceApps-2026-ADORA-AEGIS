"""Prepare synchronized synthetic records and persist complete analysis snapshots."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import HealthAnalysis, SensorReading
from app.schemas.analysis import AnalysisRead, AnalysisRequest
from app.schemas.sensor import SensorRead
from app.services.astronaut_service import get_astronaut
from app.services.errors import ConflictError, NotFoundError
from app.services.ml_adapter import MLAdapter

SENSORS = ("heart_rate", "spo2", "skin_temperature")


def prepare_input(session: Session, astronaut_id: str, request: AnalysisRequest):
    get_astronaut(session, astronaut_id)
    if not request.source.startswith("synthetic"):
        raise ConflictError("This ML handoff supports declared synthetic sources only")
    filters = (SensorReading.astronaut_id == astronaut_id,
               SensorReading.source == request.source,
               SensorReading.measurement_type.in_(
                   (*SENSORS, "temperature") if request.temperature_is_skin else SENSORS
               ))
    times_query = select(SensorReading.timestamp).where(*filters)
    if request.timestamp is not None:
        times_query = times_query.where(SensorReading.timestamp <= request.timestamp)
    times = session.scalars(times_query.distinct().order_by(SensorReading.timestamp.desc())
                            .limit(request.history_limit + 1)).all()
    if not times or (request.timestamp is not None and times[0] != request.timestamp):
        raise ConflictError("No supported readings at the requested current timestamp/source")
    rows = session.scalars(select(SensorReading).where(
        *filters, SensorReading.timestamp.in_(times)
    ).order_by(SensorReading.id)).all()
    # Latest ID per original measurement type; normalization never edits stored rows.
    chosen = {(row.timestamp, row.measurement_type): row for row in rows}
    if any(not row.is_simulated for row in chosen.values()):
        raise ConflictError("ML input contains readings not explicitly marked simulated")
    groups = {}
    snapshots = []
    notes = []
    if not request.temperature_is_skin:
        notes.append("Legacy temperature is excluded unless temperature_is_skin=true; "
                     "only explicitly labelled skin_temperature is mapped to ML temperature.")
    for (timestamp, measurement), row in chosen.items():
        group = groups.setdefault(timestamp, dict(
            astronaut_id=astronaut_id, timestamp=timestamp.isoformat(), data_source=request.source
        ))
        snapshots.append(SensorRead.model_validate(row).model_dump(mode="json"))
        if measurement == "temperature" and (timestamp, "skin_temperature") in chosen:
            notes.append(f"Reading {row.id}: legacy temperature superseded by skin_temperature "
                         "at the same timestamp, regardless of database insertion order.")
            continue
        target = "temperature" if measurement == "skin_temperature" else measurement
        unit = row.unit
        if measurement == "heart_rate" and unit == "bpm":
            unit = "beats/min"
            notes.append(f"Reading {row.id}: bpm normalized to beats/min for ML only.")
        if measurement == "skin_temperature":
            notes.append(f"Reading {row.id}: skin_temperature mapped to ML temperature.")
        elif measurement == "temperature":
            notes.append(f"Reading {row.id}: legacy temperature explicitly confirmed as skin.")
        group[target] = {"value": row.value, "unit": unit}
    current = groups[times[0]]
    current["history"] = [groups[time] for time in sorted(times[1:])]
    return current, snapshots, notes


def as_response(record: HealthAnalysis) -> AnalysisRead:
    return AnalysisRead(id=record.id, **record.result)


def create_analysis(session: Session, astronaut_id: str, request: AnalysisRequest,
                    adapter: MLAdapter) -> AnalysisRead:
    payload, snapshots, notes = prepare_input(session, astronaut_id, request)
    result = adapter.analyze(payload, snapshots, request.mode)
    result.preparation_notes = notes
    record = HealthAnalysis(
        astronaut_id=astronaut_id, analysis_timestamp=result.analysis_timestamp,
        result=result.model_dump(mode="json"),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return as_response(record)


def list_analyses(session: Session, astronaut_id: str, limit: int, offset: int):
    get_astronaut(session, astronaut_id)
    records = session.scalars(select(HealthAnalysis).where(
        HealthAnalysis.astronaut_id == astronaut_id
    ).order_by(HealthAnalysis.analysis_timestamp.desc(), HealthAnalysis.id.desc())
        .limit(limit).offset(offset)).all()
    return [as_response(record) for record in records]


def get_analysis(session: Session, astronaut_id: str, analysis_id: int):
    get_astronaut(session, astronaut_id)
    record = session.get(HealthAnalysis, analysis_id)
    if record is None or record.astronaut_id != astronaut_id:
        raise NotFoundError("Analysis not found for this astronaut")
    return as_response(record)
