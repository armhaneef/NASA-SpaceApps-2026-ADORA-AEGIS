"""Local database setup. Importing this module does not create tables."""

from collections.abc import Iterator
import logging
import os
from pathlib import Path

from sqlalchemy import URL, Engine, create_engine, event
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Session

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "aegis.sqlite3"
DATABASE_PATH = Path(os.environ.get("AEGIS_DATABASE_PATH") or DEFAULT_DATABASE_PATH).expanduser().resolve()
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Common base for SQLAlchemy table definitions."""


def create_sqlite_engine(path: str | Path = DATABASE_PATH) -> Engine:
    """Create an engine; callers can supply a temporary file for tests."""
    database_engine = create_engine(
        URL.create("sqlite", database=str(path)),
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(database_engine, "connect")
    def enable_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return database_engine


engine = create_sqlite_engine()


def init_db(database_engine: Engine = engine) -> None:
    """Create missing tables and add duplicate protection without deleting data."""
    from app.models import models  # noqa: F401: register tables before creation

    Base.metadata.create_all(database_engine)
    if database_engine.dialect.name != "sqlite":
        return

    with database_engine.connect() as connection:
        duplicate = connection.execute(text(
            """SELECT 1 FROM sensor_readings
               GROUP BY astronaut_id, timestamp, measurement_type, source, sensor_type
               HAVING COUNT(*) > 1 LIMIT 1"""
        )).first()
    if duplicate:
        logger.warning(
            "Existing duplicate sensor identities found; preserving all rows and "
            "skipping the unique index. New ingestion still checks for conflicts."
        )
        return

    identity_index = next(
        index for index in models.SensorReading.__table__.indexes
        if index.name == "uq_sensor_readings_identity"
    )
    identity_index.create(database_engine, checkfirst=True)


def get_session() -> Iterator[Session]:
    """Provide one session per future API request; callers explicitly commit."""
    with Session(engine) as session:
        yield session
