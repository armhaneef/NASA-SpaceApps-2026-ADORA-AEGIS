"""Local database setup. Importing this module does not create tables."""

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import URL, Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session

DATABASE_PATH = Path(__file__).resolve().parents[2] / "aegis.sqlite3"


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
    """Create missing tables without replacing existing data."""
    from app.models import models  # noqa: F401: register tables before creation

    Base.metadata.create_all(database_engine)


def get_session() -> Iterator[Session]:
    """Provide one session per future API request; callers explicitly commit."""
    with Session(engine) as session:
        yield session
