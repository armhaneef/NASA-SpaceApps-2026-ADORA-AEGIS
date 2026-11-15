"""Exercise the real data-engine mapping against disposable backend storage."""

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPOSITORY_ROOT / "ml-engine"
sys.path.insert(0, str(REPOSITORY_ROOT / "data-engine"))
sys.path.insert(0, str(REPOSITORY_ROOT / "data-engine" / "generators"))

from adapters.backend_ingest import to_backend_payload  # noqa: E402
from generate_synthetic_data import generate_readings  # noqa: E402


def test_generated_record_ingests_and_retrieves_as_synthetic(client):
    profile = {
        "astronaut_id": "AST-001",
        "name": "Synthetic Demonstration Astronaut",
        "mission_id": "AEGIS-DEMO",
        "mission_role": "synthetic software demonstration",
        "profile_metadata": {"data_source": "synthetic_data_engine", "is_simulated": True},
    }
    assert client.post("/astronauts", json=profile).status_code == 201

    generated = generate_readings(1, scenario="normal", seed=42)[0]
    payload = to_backend_payload(generated)
    response = client.post("/health/ingest", json=payload)
    assert response.status_code == 201
    stored = response.json()
    assert {reading["measurement_type"] for reading in stored} == {
        "heart_rate", "spo2", "skin_temperature", "respiration_rate",
    }
    assert all(reading["is_simulated"] is True for reading in stored)
    assert all(reading["source"] == "synthetic_data_engine" for reading in stored)
    assert all(reading["timestamp"] == generated["timestamp"] for reading in stored)
    assert "temperature" not in {reading["measurement_type"] for reading in stored}
    assert next(row["value"] for row in stored
                if row["measurement_type"] == "skin_temperature") == generated["skin_temperature_c"]

    latest = client.get("/health/AST-001/latest").json()
    assert len(latest) == 4
    assert {reading["measurement_type"] for reading in latest} == {
        "heart_rate", "spo2", "skin_temperature", "respiration_rate",
    }
    history = client.get("/health/AST-001/history?measurement_type=heart_rate").json()
    assert len(history) == 1
    assert history[0]["value"] == generated["heart_rate_bpm"]

    retry = client.post("/health/ingest", json=payload)
    assert retry.status_code == 200
    assert retry.json() == stored
    assert len(client.get("/health/AST-001/history").json()) == 4

    conflicting = to_backend_payload(generated | {"heart_rate_bpm": generated["heart_rate_bpm"] + 1})
    assert client.post("/health/ingest", json=conflicting).status_code == 409
    assert len(client.get("/health/AST-001/history").json()) == 4


def test_generated_complete_synthetic_history_runs_evaluable_real_local_ml(client, monkeypatch):
    monkeypatch.syspath_prepend(str(ML_ROOT))
    profile = {
        "astronaut_id": "AST-ML-ADAPTER",
        "name": "Synthetic ML Adapter Test",
        "mission_id": "AEGIS-DEMO",
        "mission_role": "synthetic software demonstration",
        "profile_metadata": {"data_source": "synthetic_data_engine", "is_simulated": True},
    }
    assert client.post("/astronauts", json=profile).status_code == 201
    records = [
        {**record, "astronaut_id": "AST-ML-ADAPTER"}
        for record in generate_readings(40, scenario="normal", seed=2026)
    ]
    for record in records:
        assert client.post("/health/ingest", json=to_backend_payload(record)).status_code == 201

    response = client.post("/health/AST-ML-ADAPTER/analyses", json={
        "mode": "local", "source": "synthetic_data_engine", "history_limit": 100,
        "temperature_is_skin": False,
    })
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["is_mock"] is False
    assert result["status"] in {"normal", "anomaly"}
    assert result["ml_result"] is not None
    assert result["is_mock"] is False
    assert result["model_version"] == "2.0.0"
    assert result["anomaly_detected"] is (result["status"] == "anomaly")
    assert result["prepared_input"]["data_source"] == "synthetic_data_engine"
    assert result["ml_result"]["data_quality"]["status"] == "valid"
    assert result["ml_result"]["data_quality"]["history_records_accepted"] == 39
    assert "temperature" not in result["ml_result"]["data_quality"]["errors"]
    assert len(result["prepared_input"]["history"]) == 39


def test_missing_synthetic_skin_temperature_remains_insufficient_data(client, monkeypatch):
    monkeypatch.syspath_prepend(str(ML_ROOT))
    astronaut_id = "AST-ML-MISSING-TEMP"
    profile = {
        "astronaut_id": astronaut_id,
        "name": "Synthetic Incomplete History Test",
        "mission_id": "AEGIS-DEMO",
        "mission_role": "synthetic software demonstration",
        "profile_metadata": {"data_source": "synthetic_data_engine", "is_simulated": True},
    }
    assert client.post("/astronauts", json=profile).status_code == 201
    timestamp = "2026-01-01T00:00:00Z"
    for measurement, value, unit in (
        ("heart_rate", 72, "bpm"), ("spo2", 98, "%"),
    ):
        assert client.post("/health/ingest", json={
            "astronaut_id": astronaut_id, "timestamp": timestamp,
            "sensor_type": "synthetic_multi_sensor", "measurement_type": measurement,
            "value": value, "unit": unit, "source": "synthetic_data_engine",
            "is_simulated": True,
        }).status_code == 201
    response = client.post(f"/health/{astronaut_id}/analyses", json={
        "mode": "local", "source": "synthetic_data_engine", "history_limit": 100,
    })
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["is_mock"] is False
    assert result["status"] == "insufficient_data"
    assert result["anomaly_detected"] is None
    assert result["ml_result"]["data_quality"]["errors"]["temperature"] == "missing reading"
