"""Verify persistence and storage integrity using temporary SQLite files."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session

from app.database.connection import init_db
from app.models.models import Astronaut, SensorReading


def astronaut():
    return Astronaut(
        astronaut_id="AST-001", name="Mira Sen (fictional)",
        mission_id="MARS-SIM-01", mission_role="Engineer",
        profile_metadata={"fictional": True},
    )


def reading(**overrides):
    values = dict(
        astronaut_id="AST-001",
        timestamp=datetime(2026, 11, 14, 10, tzinfo=timezone(timedelta(hours=5, minutes=30))),
        sensor_type="smart_band", measurement_type="heart_rate", value=78,
        unit="beats/min", source="synthetic_example", is_simulated=True,
    )
    values.update(overrides)
    return SensorReading(**values)


def test_save_and_retrieve_astronaut(database_engine):
    with Session(database_engine) as session:
        session.add(astronaut())
        session.commit()
    init_db(database_engine)  # restarting initialization preserves records
    with Session(database_engine) as session:
        saved = session.get(Astronaut, "AST-001")
        assert saved.name == "Mira Sen (fictional)"
        assert saved.mission_id == "MARS-SIM-01"
        assert saved.mission_role == "Engineer"
        assert saved.profile_metadata == {"fictional": True}
        assert saved.created_at.utcoffset() == timedelta(0)
        assert session.get(Astronaut, "missing") is None
        assert len(session.scalars(select(Astronaut)).all()) == 1


def test_sensor_metadata_and_relationship(database_engine):
    with Session(database_engine) as session:
        person = astronaut()
        person.sensor_readings.append(reading())
        session.add(person)
        session.commit()
    with Session(database_engine) as session:
        saved = session.get(Astronaut, "AST-001").sensor_readings[0]
        assert saved.timestamp == datetime(2026, 11, 14, 4, 30, tzinfo=timezone.utc)
        assert (saved.value, saved.unit, saved.source) == (78, "beats/min", "synthetic_example")
        assert saved.is_simulated is True
        assert saved.sensor_type == "smart_band"
        assert saved.measurement_type == "heart_rate"


def test_unknown_astronaut_rejected(database_engine):
    with Session(database_engine) as session:
        session.add(reading())
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_duplicate_astronaut_rejected(database_engine):
    with Session(database_engine) as session:
        session.add(astronaut())
        session.commit()
        session.add(astronaut())
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_naive_timestamp_rejected(database_engine):
    with Session(database_engine) as session:
        session.add(astronaut())
        session.commit()
        session.add(reading(timestamp=datetime(2026, 11, 14)))
        with pytest.raises(StatementError, match="timezone"):
            session.commit()
        session.rollback()


def test_initial_tables(database_engine):
    assert set(inspect(database_engine).get_table_names()) == {
        "astronauts", "sensor_readings", "health_analyses"
    }
