"""API validation, atomic ingestion, filtering, and latest semantics."""

import pytest

PROFILE = {"astronaut_id": "AST-001", "name": "Fictional Astronaut",
           "mission_id": "MARS-SIM-01", "mission_role": "Engineer"}
READING = {"astronaut_id": "AST-001", "timestamp": "2026-11-14T10:00:00Z",
           "sensor_type": "smart_band", "measurement_type": "heart_rate",
           "value": 78, "unit": "beats/min", "source": "synthetic_example",
           "is_simulated": True, "quality": "simulated"}


@pytest.fixture
def astronaut_client(client):
    assert client.post("/astronauts", json=PROFILE).status_code == 201
    return client


def test_ingest_and_retrieve(astronaut_client):
    client = astronaut_client
    response = client.post("/health/ingest", json=READING)
    assert response.status_code == 201
    record = response.json()[0]
    for key in READING:
        if key != "timestamp":
            assert record[key] == READING[key]
    assert client.get("/health/AST-001/latest").json() == [record]
    assert client.get("/health/AST-001/history").json() == [record]
    assert client.delete("/astronauts/AST-001").status_code == 409
    assert client.get("/health/AST-001/history").json() == [record]


@pytest.mark.parametrize("changes", [
    {"timestamp": "bad"}, {"timestamp": "2026-11-14T10:00:00"},
    {"measurement_type": "ecg_waveform"}, {"unit": "wrong"},
    {"value": -1}, {"value": True}, {"value": "78"},
    {"measurement_type": "spo2", "unit": "%", "value": 101},
    {"source": " "}, {"sensor_type": ""}, {"is_simulated": "true"},
    {"quality": ""}, {"extra": 1},
])
def test_invalid_reading_is_not_saved(astronaut_client, changes):
    client = astronaut_client
    assert client.post("/health/ingest", json=READING | changes).status_code == 422
    assert client.get("/health/AST-001/history").json() == []


@pytest.mark.parametrize("field", ["source", "is_simulated", "timestamp", "unit"])
def test_required_metadata(astronaut_client, field):
    payload = READING.copy()
    payload.pop(field)
    assert astronaut_client.post("/health/ingest", json=payload).status_code == 422


def test_unknown_astronaut(client):
    assert client.post("/health/ingest", json=READING).status_code == 404
    for endpoint in ("latest", "history"):
        assert client.get(f"/health/missing/{endpoint}").status_code == 404


def test_empty_readings(astronaut_client):
    for endpoint in ("latest", "history"):
        response = astronaut_client.get(f"/health/AST-001/{endpoint}")
        assert response.status_code == 200
        assert response.json() == []


def test_grouped_ingestion_atomic(astronaut_client):
    payload = {key: READING[key] for key in
               ("astronaut_id", "timestamp", "sensor_type", "is_simulated")}
    payload.update(data_source="synthetic_example", heart_rate={"value": 78, "unit": "beats/min"},
                   spo2={"value": 98, "unit": "%"})
    invalid = payload | {"spo2": {"value": 101, "unit": "%"}}
    assert astronaut_client.post("/health/ingest", json=invalid).status_code == 422
    assert astronaut_client.get("/health/AST-001/history").json() == []
    response = astronaut_client.post("/health/ingest", json=payload)
    assert response.status_code == 201
    assert len(response.json()) == 2
    assert {row["source"] for row in response.json()} == {"synthetic_example"}


@pytest.mark.parametrize("measurements", [{}, {"heart_rate": None}])
def test_empty_or_null_group_rejected(astronaut_client, measurements):
    payload = {key: READING[key] for key in
               ("astronaut_id", "timestamp", "sensor_type", "is_simulated")}
    payload.update(data_source="synthetic_example", **measurements)
    assert astronaut_client.post("/health/ingest", json=payload).status_code == 422


def test_latest_invalid_type(astronaut_client):
    assert astronaut_client.get("/health/AST-001/latest?measurement_type=unknown").status_code == 422


def test_latest_and_history_filters(astronaut_client):
    client = astronaut_client
    # Deliberately insert an older measurement after a newer one.
    for payload in [READING | {"timestamp": "2026-11-14T11:00:00Z", "value": 80},
                    READING, READING | {"value": 81, "timestamp": "2026-11-14T11:00:00Z"},
                    READING | {"measurement_type": "spo2", "value": 98, "unit": "%"}]:
        assert client.post("/health/ingest", json=payload).status_code == 201
    latest = client.get("/health/AST-001/latest").json()
    assert [(row["measurement_type"], row["value"]) for row in latest] == [
        ("heart_rate", 81), ("spo2", 98)]
    assert len(client.get("/health/AST-001/latest?measurement_type=spo2").json()) == 1
    history = client.get("/health/AST-001/history", params={
        "measurement_type": "heart_rate", "start": "2026-11-14T15:30:00+05:30",
        "end": "2026-11-14T11:00:00Z", "limit": 1, "offset": 1,
    }).json()
    assert len(history) == 1 and history[0]["value"] == 80
    assert client.get("/health/AST-001/history?measurement_type=co2").json() == []
    client.post("/astronauts", json=PROFILE | {"astronaut_id": "AST-002"})
    assert client.get("/health/AST-002/latest").json() == []


@pytest.mark.parametrize("query", ["start=bad", "start=2026-11-14T10:00:00", "limit=0",
                                  "limit=1001", "offset=-1", "measurement_type=unknown",
                                  "start=2026-11-15T00:00:00Z&end=2026-11-14T00:00:00Z"])
def test_invalid_history_queries(astronaut_client, query):
    assert astronaut_client.get(f"/health/AST-001/history?{query}").status_code == 422


def test_nonfinite_value_rejected(astronaut_client):
    import json
    content = json.dumps(READING).replace('"value": 78', '"value": 1e999')
    assert astronaut_client.post("/health/ingest", content=content,
                                 headers={"Content-Type": "application/json"}).status_code == 422
