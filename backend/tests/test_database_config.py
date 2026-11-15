"""Runtime SQLite path selection and non-destructive index bootstrap tests."""

import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.database.connection import create_sqlite_engine, init_db
from app.models.models import Astronaut, SensorReading


BACKEND = Path(__file__).resolve().parents[1]


def test_database_path_environment_is_applied_before_engine_initialization(tmp_path):
    database = tmp_path / "disposable" / "aegis-demo.sqlite3"
    environment = os.environ.copy()
    environment["AEGIS_DATABASE_PATH"] = str(database)
    environment["PYTHONPATH"] = str(BACKEND) + os.pathsep + environment.get("PYTHONPATH", "")
    script = (
        "from app.database.connection import DATABASE_PATH, engine; "
        "print(DATABASE_PATH); print(engine.url.database)"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=BACKEND, env=environment,
        capture_output=True, text=True, check=True,
    )
    configured_path, engine_path = result.stdout.strip().splitlines()
    assert Path(configured_path) == database.resolve()
    assert Path(engine_path) == database.resolve()
    assert not database.exists()


def test_existing_duplicate_rows_are_preserved_and_unique_index_is_skipped(tmp_path, caplog):
    database_engine = create_sqlite_engine(tmp_path / "legacy.sqlite3")
    init_db(database_engine)
    with database_engine.begin() as connection:
        connection.exec_driver_sql("DROP INDEX uq_sensor_readings_identity")
    with Session(database_engine) as session:
        session.add(Astronaut(
            astronaut_id="AST-LEGACY", name="Synthetic", mission_id="DEMO",
            mission_role="test", profile_metadata={},
        ))
        session.commit()
        values = dict(
            astronaut_id="AST-LEGACY",
            timestamp=datetime(2026, 11, 14, 10, tzinfo=timezone.utc),
            sensor_type="fixture", measurement_type="heart_rate", value=72,
            unit="bpm", source="synthetic_legacy", is_simulated=True, quality=None,
        )
        session.add_all([SensorReading(**values), SensorReading(**values)])
        session.commit()

    init_db(database_engine)
    with Session(database_engine) as session:
        assert len(session.scalars(select(SensorReading)).all()) == 2
    indexes = inspect(database_engine).get_indexes("sensor_readings")
    assert "uq_sensor_readings_identity" not in {index["name"] for index in indexes}
    assert "preserving all rows" in caplog.text
    database_engine.dispose()
