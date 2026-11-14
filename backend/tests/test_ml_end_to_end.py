"""Real HTTP -> ingestion -> SQLite -> Member 2 ML -> saved analysis tests.

The subprocess uses the actual FastAPI app and local ML dependency, not an ML
stub. Only its database dependency is redirected to a temporary SQLite file.
"""

import json as json_lib
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest

BACKEND = Path(__file__).resolve().parents[1]
ML_DIRECTORY = BACKEND.parent / "ml-engine"


class HTTPClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def request(self, method, path, payload=None):
        body = json_lib.dumps(payload).encode() if payload is not None else None
        request = Request(self.base_url + path, data=body, method=method,
                          headers={"Content-Type": "application/json"})
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            text = response.read().decode()
            return SimpleNamespace(status_code=response.status, text=text,
                                   json=lambda: json_lib.loads(text))

    def post(self, path, *, json):
        return self.request("POST", path, json)

    def get(self, path):
        return self.request("GET", path)


@pytest.fixture(scope="module")
def runtime_client(tmp_path_factory):
    pytest.importorskip("sklearn", reason="Install requirements-ml.txt for real HTTP ML tests")
    if not (ML_DIRECTORY / "aegis_ml").is_dir():
        pytest.skip("Sibling ML implementation is not checked out")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    database = tmp_path_factory.mktemp("ml-runtime") / "runtime.sqlite3"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ML_DIRECTORY) + os.pathsep + environment.get("PYTHONPATH", "")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    bootstrap = """
import sys
import uvicorn
from sqlalchemy.orm import Session
import app.main as main
from app.database.connection import create_sqlite_engine, init_db, get_session
from aegis_ml import analyze_health
engine = create_sqlite_engine(sys.argv[1])
main.init_db = lambda: init_db(engine)
def session_override():
    with Session(engine) as session:
        yield session
main.app.dependency_overrides[get_session] = session_override
uvicorn.run(main.app, host='127.0.0.1', port=int(sys.argv[2]), log_level='error', access_log=False)
"""
    process = subprocess.Popen(
        [sys.executable, "-B", "-c", bootstrap, str(database), str(port)],
        cwd=BACKEND, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    client = HTTPClient(f"http://127.0.0.1:{port}")
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and process.poll() is None:
            try:
                if client.get("/health").status_code == 200:
                    break
            except (URLError, TimeoutError):
                time.sleep(0.1)
        else:
            if process.poll() is None:
                process.terminate()
            output, _ = process.communicate(timeout=10)
            pytest.fail(f"Real FastAPI/ML runtime failed to start: {output.decode()}")
        yield client
    finally:
        if process.poll() is None:
            process.terminate()
        process.communicate(timeout=10)


def profile(client):
    identifier = "AST-E2E-" + uuid4().hex[:12]
    response = client.post("/astronauts", json={
        "astronaut_id": identifier, "name": "Fictional integration astronaut",
        "mission_id": "MARS-SIM", "mission_role": "Engineer",
    })
    assert response.status_code == 201, response.text
    return identifier


def reading(client, identifier, timestamp, measurement, value, unit):
    response = client.post("/health/ingest", json={
        "astronaut_id": identifier, "timestamp": timestamp,
        "sensor_type": "synthetic_multi_sensor", "measurement_type": measurement,
        "value": value, "unit": unit, "source": "synthetic_example", "is_simulated": True,
    })
    assert response.status_code == 201, response.text
    return response.json()[0]


def analyze(client, identifier, **options):
    url = f"/health/{identifier}/analyses"
    response = client.post(url, json={"mode": "local", "source": "synthetic_example", **options})
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["is_mock"] is False
    assert client.get(url + f"/{result['id']}").json() == result
    assert client.get(url + "/latest").json() == result
    assert client.get(url).json()[0] == result
    return result


@pytest.mark.parametrize("fixture,status,history_limit,forest", [
    ("normal", "normal", 100, False),
    ("anomaly", "anomaly", 100, False),
    ("normal", "insufficient_data", 0, False),
    ("isolation_normal", "normal", 100, True),
    ("isolation_anomaly", "anomaly", 100, True),
])
def test_ingestion_history_real_ml_saved_analysis(runtime_client, fixture, status, history_limit, forest):
    client = runtime_client
    identifier = profile(client)
    example = json_lib.loads((ML_DIRECTORY / "examples" / f"{fixture}.json").read_text())
    records = [*example["history"], example]
    for record in records:
        for measurement in ("heart_rate", "spo2", "temperature"):
            value = record[measurement]["value"]
            target = "skin_temperature" if measurement == "temperature" else measurement
            unit = "bpm" if measurement == "heart_rate" else record[measurement]["unit"]
            reading(client, identifier, record["timestamp"], target, value, unit)
    # A second astronaut with an extreme historical measurement must not affect this baseline.
    other = profile(client)
    reading(client, other, records[0]["timestamp"], "heart_rate", 240, "bpm")
    result = analyze(client, identifier, history_limit=history_limit)
    raw = result["ml_result"]
    assert result["status"] == status
    assert result["anomaly_detected"] is ({"normal": False, "anomaly": True, "insufficient_data": None}[status])
    assert (result["anomaly_score"] is None) == (status == "insufficient_data")
    expected_count = min(len(example["history"]), history_limit)
    assert raw["data_quality"]["history_records_received"] == expected_count
    assert raw["data_quality"]["history_records_accepted"] == expected_count
    assert raw["data_quality"]["status"] == "valid"
    assert raw["model"]["isolation_forest"]["used"] is forest
    if forest:
        assert expected_count >= 32
        assert raw["model"]["isolation_forest"]["training_records"] == expected_count
        assert raw["anomaly"]["method"] == "isolation_forest"
    else:
        assert raw["anomaly"]["method"] == "personalized_baseline_deviation"
    for sensor in ("heart_rate", "spo2", "temperature"):
        assert raw["baseline"][sensor]["count"] == expected_count
    prepared = result["prepared_input"]
    assert prepared["heart_rate"]["unit"] == "beats/min"
    assert prepared["temperature"] == example["temperature"]
    assert all(record["astronaut_id"] == identifier for record in prepared["history"])
    assert all(record["timestamp"] < prepared["timestamp"] for record in prepared["history"])
    history = client.get(f"/health/{identifier}/history?limit=1000").json()
    assert len(history) == len(records) * 3
    assert all(row["unit"] == "bpm" for row in history if row["measurement_type"] == "heart_rate")
    assert any(row["measurement_type"] == "skin_temperature" for row in result["input_readings"])
    assert any("normalized" in note for note in result["preparation_notes"])
    assert client.get(f"/health/{other}/analyses/{result['id']}").status_code == 404


@pytest.mark.parametrize("reverse", [False, True])
def test_temperature_precedence_and_explicit_legacy_semantics(runtime_client, reverse):
    client = runtime_client
    identifier = profile(client)
    timestamp = "2026-11-14T10:00:00Z"
    reading(client, identifier, timestamp, "heart_rate", 78, "bpm")
    pairs = [("temperature", 37), ("skin_temperature", 33)]
    for measurement, value in reversed(pairs) if reverse else pairs:
        reading(client, identifier, timestamp, measurement, value, "degC")
    result = analyze(client, identifier, temperature_is_skin=True)
    assert result["prepared_input"]["temperature"]["value"] == 33
    assert any("superseded" in note for note in result["preparation_notes"])
    # Legacy temperature alone is excluded until the caller confirms it is skin.
    legacy = profile(client)
    reading(client, legacy, timestamp, "heart_rate", 78, "bpm")
    reading(client, legacy, timestamp, "temperature", 37, "degC")
    unconfirmed = analyze(client, legacy)
    assert "temperature" not in unconfirmed["prepared_input"]
    assert "temperature" in unconfirmed["ml_result"]["data_quality"]["errors"]
    confirmed = analyze(client, legacy, temperature_is_skin=True)
    assert confirmed["prepared_input"]["temperature"]["value"] == 37


@pytest.mark.parametrize("heart_rate,temperature", [(19, 9), (251, 51)])
def test_out_of_ml_domain_remains_raw_and_returns_quality_errors(runtime_client, heart_rate, temperature):
    client = runtime_client
    identifier = profile(client)
    timestamp = "2026-11-14T10:00:00Z"
    reading(client, identifier, timestamp, "heart_rate", heart_rate, "bpm")
    reading(client, identifier, timestamp, "skin_temperature", temperature, "degC")
    reading(client, identifier, timestamp, "spo2", 98, "%")
    result = analyze(client, identifier)
    assert result["status"] == "insufficient_data"
    assert result["anomaly_detected"] is None and result["anomaly_score"] is None
    assert result["prepared_input"]["heart_rate"]["value"] == heart_rate
    assert result["prepared_input"]["temperature"]["value"] == temperature
    quality = result["ml_result"]["data_quality"]
    assert quality["status"] == "partial"
    assert "[20, 250]" in quality["errors"]["heart_rate"]
    assert "[10, 50]" in quality["errors"]["temperature"]
    assert result["ml_result"]["sensor_readings"]["heart_rate"]["value"] is None
    assert result["ml_result"]["sensor_readings"]["temperature"]["value"] is None
    history = client.get(f"/health/{identifier}/history").json()
    assert next(row for row in history if row["measurement_type"] == "heart_rate")["value"] == heart_rate


@pytest.mark.parametrize("heart_rate,temperature", [(20, 10), (250, 50)])
def test_ml_input_boundaries_are_inclusive(runtime_client, heart_rate, temperature):
    client = runtime_client
    identifier = profile(client)
    timestamp = "2026-11-14T10:00:00Z"
    for measurement, value, unit in (("heart_rate", heart_rate, "bpm"),
                                      ("skin_temperature", temperature, "degC"), ("spo2", 98, "%")):
        reading(client, identifier, timestamp, measurement, value, unit)
    result = analyze(client, identifier)
    assert result["ml_result"]["data_quality"]["status"] == "valid"
    assert result["ml_result"]["sensor_readings"]["temperature"]["value"] == temperature
