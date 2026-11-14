"""Keep every test away from the demonstration database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.connection import create_sqlite_engine, get_session, init_db
from app.main import app


@pytest.fixture
def database_engine(tmp_path):
    engine = create_sqlite_engine(tmp_path / "test.sqlite3")
    init_db(engine)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def isolate_app_database(monkeypatch, database_engine):
    monkeypatch.setattr("app.main.init_db", lambda: init_db(database_engine))
    def test_session():
        with Session(database_engine) as session:
            yield session
    app.dependency_overrides[get_session] = test_session
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
