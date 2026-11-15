"""Atomic ingestion and ordered sensor queries."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import SensorReading
from app.schemas.sensor import SensorCreate
from app.services.astronaut_service import get_astronaut
from app.services.errors import ConflictError


def ingest(session: Session, readings: list[SensorCreate]):
    """Insert new identities, reuse exact retries, and reject changed retries.

    Returns ``(records, created)``. The identity includes the source and sensor
    stream, so independent streams at one instant remain separate. Existing
    rows are never updated or deleted.
    """
    for astronaut_id in {item.astronaut_id for item in readings}:
        get_astronaut(session, astronaut_id)

    unique_readings = {}
    for reading in readings:
        key = _identity(reading)
        previous = unique_readings.get(key)
        if previous is not None and not _same_measurement(previous, reading):
            raise ConflictError("The batch contains different values for the same sensor identity")
        unique_readings[key] = reading

    records_by_identity = {}
    new_records = []
    for key, reading in unique_readings.items():
        existing = _find_identity(session, reading)
        if len(existing) > 1:
            raise ConflictError(
                "The database already contains duplicate sensor identities; "
                "existing readings were preserved"
            )
        if existing:
            record = existing[0]
            if not _same_measurement(record, reading):
                raise ConflictError(
                    "A reading already exists for this sensor identity with different content"
                )
            records_by_identity[key] = record
        else:
            record = SensorReading(**reading.model_dump())
            records_by_identity[key] = record
            new_records.append(record)

    created = False
    if new_records:
        session.add_all(new_records)
        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            # A competing request may have inserted the same exact readings.
            # Reuse those rows after the unique index rejects this transaction.
            for key, reading in unique_readings.items():
                existing = _find_identity(session, reading)
                if len(existing) != 1 or not _same_measurement(existing[0], reading):
                    raise ConflictError(
                        "A concurrent reading has a different value; retry with a new timestamp"
                    ) from error
                records_by_identity[key] = existing[0]
        else:
            created = True
            for record in new_records:
                session.refresh(record)
    return [records_by_identity[_identity(item)] for item in unique_readings.values()], created


def _identity(reading):
    return (
        reading.astronaut_id, reading.timestamp, reading.measurement_type,
        reading.source, reading.sensor_type,
    )


def _same_measurement(existing, incoming):
    return all(getattr(existing, field) == getattr(incoming, field) for field in (
        "value", "unit", "is_simulated", "quality",
    ))


def _find_identity(session: Session, reading: SensorCreate):
    return session.scalars(select(SensorReading).where(
        SensorReading.astronaut_id == reading.astronaut_id,
        SensorReading.timestamp == reading.timestamp,
        SensorReading.measurement_type == reading.measurement_type,
        SensorReading.source == reading.source,
        SensorReading.sensor_type == reading.sensor_type,
    )).all()


def history(session: Session, astronaut_id: str, measurement_type: str | None,
            start: datetime | None, end: datetime | None, limit: int, offset: int):
    get_astronaut(session, astronaut_id)
    query = select(SensorReading).where(SensorReading.astronaut_id == astronaut_id)
    if measurement_type is not None:
        query = query.where(SensorReading.measurement_type == measurement_type)
    if start is not None:
        query = query.where(SensorReading.timestamp >= start)
    if end is not None:
        query = query.where(SensorReading.timestamp <= end)
    return session.scalars(query.order_by(SensorReading.timestamp, SensorReading.id)
                           .limit(limit).offset(offset)).all()


def latest(session: Session, astronaut_id: str, measurement_type: str | None):
    get_astronaut(session, astronaut_id)
    ranked = select(
        SensorReading.id,
        func.row_number().over(
            partition_by=SensorReading.measurement_type,
            order_by=(SensorReading.timestamp.desc(), SensorReading.id.desc()),
        ).label("rank"),
    ).where(SensorReading.astronaut_id == astronaut_id)
    if measurement_type is not None:
        ranked = ranked.where(SensorReading.measurement_type == measurement_type)
    ranked = ranked.subquery()
    return session.scalars(select(SensorReading).join(ranked, SensorReading.id == ranked.c.id)
                           .where(ranked.c.rank == 1)
                           .order_by(SensorReading.measurement_type)).all()
