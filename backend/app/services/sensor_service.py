"""Atomic ingestion and ordered sensor queries."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.models import SensorReading
from app.schemas.sensor import SensorCreate
from app.services.astronaut_service import get_astronaut


def ingest(session: Session, readings: list[SensorCreate]):
    for astronaut_id in {item.astronaut_id for item in readings}:
        get_astronaut(session, astronaut_id)
    records = [SensorReading(**item.model_dump()) for item in readings]
    session.add_all(records)
    session.commit()
    for record in records:
        session.refresh(record)
    return records


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
