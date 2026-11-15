"""Analysis API, preparation policy, persistence, and ML failure handling."""

import copy
from types import SimpleNamespace

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.models import SensorReading

PROFILE = {"astronaut_id": "AST-ML", "name": "Fictional ML Astronaut",
           "mission_id": "MARS-SIM", "mission_role": "Engineer"}
READING = {"astronaut_id": "AST-ML", "timestamp": "2026-11-14T10:00:00Z",
           "sensor_type": "synthetic_multi_sensor", "source": "synthetic_example",
           "measurement_type": "heart_rate", "value": 78, "unit": "beats/min",
           "is_simulated": True}
URL = "/health/AST-ML/analyses"
REQUEST = {"mode": "mock", "source": "synthetic_example"}


@pytest.fixture
def seeded(client):
    assert client.post("/astronauts", json=PROFILE).status_code == 201
    assert client.post("/health/ingest", json=READING).status_code == 201
    return client


def valid_output(payload):
    """Contract-shaped stub, not an implementation of Member 2's model."""
    units = {"heart_rate": "beats/min", "spo2": "%", "temperature": "degC"}
    return {
        "schema_version": "1.0", **{key: payload[key] for key in
                                  ("astronaut_id", "timestamp", "data_source")},
        "sensor_readings": {key: {"value": None, "unit": unit} for key, unit in units.items()},
        "baseline": {key: dict(count=0, mean=None, std=None, scale=None, unit=unit, ready=False)
                     for key, unit in units.items()},
        "anomaly": {"status": "insufficient_data", "is_anomaly": None,
                    "normalized_score": None, "method": "personalized_baseline_deviation",
                    "sensor_method": "personalized_baseline_deviation",
                    "sensors": {key: {"status": "insufficient_data", "deviation_score": None}
                                for key in units}},
        "trends": {key: dict(direction="unknown", count=0, slope_per_hour=None,
                             fitted_change=None, change_threshold=1, unit=unit + "/hour",
                             start_timestamp=None, end_timestamp=None) for key, unit in units.items()},
        "data_quality": dict(status="partial", errors={"spo2": "missing"}, history_issues=[],
                             history_records_received=0, history_records_accepted=0),
        "model": dict(name="personalized_baseline_deviation", version="2.0.0",
                      minimum_history_per_sensor=3, deviation_threshold=3.0,
                      synthetic_only=True, clinically_validated=False,
                      score_normalization="max_deviation / (max_deviation + 3)",
                      isolation_forest=dict(minimum_history=32, training_records=0,
                          features=list(units), random_state=42, n_estimators=100,
                          contamination=0.05, sklearn_version="test-stub", used=False,
                          fallback_reason="insufficient_complete_history", score_threshold=None)),
        "additive_field": {"preserved": True},
    }


def install_stub(monkeypatch, function):
    monkeypatch.setattr("app.services.ml_adapter.importlib.import_module",
                        lambda name: SimpleNamespace(analyze_health=function))


def test_mock_persisted_and_retrieved(seeded):
    response = seeded.post(URL, json=REQUEST)
    assert response.status_code == 201
    result = response.json()
    assert result["is_mock"] is True and result["status"] == "mock"
    assert result["anomaly_detected"] is None and result["anomaly_score"] is None
    assert "MOCK" in result["explanations"][0]
    assert result["model_version"] == "backend-mock-1.0"
    assert result["ml_result"] is None
    assert result["input_readings"][0]["is_simulated"] is True
    assert result["input_readings"][0]["source"] == "synthetic_example"
    assert seeded.get(URL + f"/{result['id']}").json() == result
    assert seeded.get(URL + "/latest").json() == result
    assert seeded.get(URL).json() == [result]
    second = seeded.post(URL, json=REQUEST).json()
    assert seeded.get(URL + "/latest").json()["id"] == second["id"]
    assert seeded.get(URL + "?limit=1&offset=1").json() == [result]


def test_local_preserves_raw_result_and_snapshot(seeded, monkeypatch):
    seen = []
    def fake(payload):
        seen.append(copy.deepcopy(payload))
        output = valid_output(payload)
        payload["history"].append({"mutated": True})
        return output
    install_stub(monkeypatch, fake)
    result = seeded.post(URL, json=REQUEST | {"mode": "local"})
    assert result.status_code == 201
    result = result.json()
    assert result["is_mock"] is False and result["status"] == "insufficient_data"
    assert result["anomaly_detected"] is None and result["anomaly_score"] is None
    assert result["prepared_input"] == seen[0]
    assert result["ml_result"] == valid_output(seen[0])
    assert seeded.get(URL + f"/{result['id']}").json() == result


def test_local_anomaly_summary_comes_from_engine(seeded, monkeypatch):
    def fake(payload):
        result = valid_output(payload)
        result["anomaly"].update(status="anomaly", is_anomaly=True, normalized_score=0.8)
        result["anomaly"]["sensors"]["heart_rate"].update(status="anomaly", deviation_score=12)
        return result
    install_stub(monkeypatch, fake)
    response = seeded.post(URL, json=REQUEST | {"mode": "local"})
    assert response.status_code == 201
    result = response.json()
    assert result["anomaly_detected"] is True
    assert result["anomaly_score"] == 0.8
    assert result["affected_measurements"] == ["heart_rate"]


@pytest.mark.parametrize("failure", ["missing", "runtime"])
def test_unavailable_never_saves_or_falls_back(seeded, monkeypatch, failure):
    if failure == "missing":
        def missing(name):
            raise ModuleNotFoundError("test unavailable")
        monkeypatch.setattr("app.services.ml_adapter.importlib.import_module", missing)
    else:
        def broken(payload):
            raise RuntimeError("secret internal failure")
        install_stub(monkeypatch, broken)
    response = seeded.post(URL, json=REQUEST | {"mode": "local"})
    assert response.status_code == 503
    assert "secret" not in response.text
    assert seeded.get(URL).json() == []
    # Explicit mock still works offline, even with the real module broken.
    assert seeded.post(URL, json=REQUEST).status_code == 201


@pytest.mark.parametrize("defect", ["missing", "identity", "nonfinite", "flag", "score", "method"])
def test_bad_ml_output_not_saved(seeded, monkeypatch, defect):
    def bad(payload):
        output = valid_output(payload)
        if defect == "missing":
            del output["trends"]
        elif defect == "identity":
            output["astronaut_id"] = "OTHER"
        elif defect == "nonfinite":
            output["additive_field"] = float("nan")
        elif defect == "flag":
            output["anomaly"]["is_anomaly"] = False
        elif defect == "score":
            output["anomaly"]["normalized_score"] = 0.4
        else:
            output["model"]["name"] = "isolation_forest"
        return output
    install_stub(monkeypatch, bad)
    assert seeded.post(URL, json=REQUEST | {"mode": "local"}).status_code == 502
    assert seeded.get(URL).json() == []


def test_no_data_and_missing_astronaut(client):
    assert client.post(URL, json=REQUEST).status_code == 404
    assert client.get(URL).status_code == 404
    client.post("/astronauts", json=PROFILE)
    assert client.post(URL, json=REQUEST).status_code == 409
    assert client.get(URL).json() == []
    assert client.get(URL + "/latest").status_code == 404
    assert client.get(URL + "/1").status_code == 404


@pytest.mark.parametrize("changes", [{"mode": "cloud"}, {"source": ""}, {"history_limit": -1},
                                     {"history_limit": 201}, {"timestamp": "2026-11-14T10:00:00"},
                                     {"temperature_is_skin": "true"},
                                     {"unknown": True}])
def test_invalid_requests(seeded, changes):
    assert seeded.post(URL, json=REQUEST | changes).status_code == 422
    assert seeded.get(URL).json() == []


def test_provenance_and_exact_timestamp(seeded):
    assert seeded.post(URL, json=REQUEST | {"source": "real"}).status_code == 409
    assert seeded.post(URL, json=REQUEST | {"timestamp": "2026-11-14T09:00:00Z"}).status_code == 409
    assert seeded.post("/health/ingest", json=READING | {
        "sensor_type": "independent_non_simulated_sensor", "is_simulated": False,
    }).status_code == 201
    assert seeded.post(URL, json=REQUEST).status_code == 409


def test_history_policy_and_isolation(seeded):
    for time in ("08:00", "09:00", "11:00"):
        seeded.post("/health/ingest", json=READING | {"timestamp": f"2026-11-14T{time}:00Z"})
    # Same-time supported measurement is grouped; asynchronous one is not carried forward.
    seeded.post("/health/ingest", json=READING | {"measurement_type": "spo2", "value": 98, "unit": "%"})
    seeded.post("/health/ingest", json=READING | {"source": "synthetic_other", "value": 200})
    seeded.post("/astronauts", json=PROFILE | {"astronaut_id": "OTHER"})
    seeded.post("/health/ingest", json=READING | {"astronaut_id": "OTHER", "value": 200})
    seeded.post("/health/ingest", json=READING | {
        "sensor_type": "independent_sensor", "value": 79,
    })
    response = seeded.post(URL, json=REQUEST | {"timestamp": READING["timestamp"], "history_limit": 1})
    assert response.status_code == 201
    payload = response.json()["prepared_input"]
    assert payload["heart_rate"]["value"] == 79
    assert payload["spo2"]["value"] == 98
    assert len(payload["history"]) == 1
    assert "09:00" in payload["history"][0]["timestamp"]
    result = seeded.post(URL, json=REQUEST | {"history_limit": 0}).json()
    assert result["prepared_input"]["history"] == []
    assert "spo2" not in result["prepared_input"]
    assert "11:00" in result["prepared_input"]["timestamp"]


def test_analysis_protects_profile_and_survives_new_session(seeded, database_engine):
    result = seeded.post(URL, json=REQUEST).json()
    # Even if readings are removed through maintenance, the analysis audit remains protected.
    with Session(database_engine) as session:
        session.execute(delete(SensorReading))
        session.commit()
    assert seeded.delete("/astronauts/AST-ML").status_code == 409
    assert seeded.get(URL + f"/{result['id']}").json() == result
    seeded.post("/astronauts", json=PROFILE | {"astronaut_id": "OTHER"})
    assert seeded.get(f"/health/OTHER/analyses/{result['id']}").status_code == 404


def test_real_local_engine_when_available(seeded, monkeypatch):
    """Optional smoke test calls Member 2's public interface, without modifying it."""
    from pathlib import Path
    pytest.importorskip("sklearn", reason="Install requirements-ml.txt for real-engine smoke test")
    module_path = Path(__file__).resolve().parents[2] / "ml-engine"
    if not (module_path / "aegis_ml").is_dir():
        pytest.skip("Optional sibling ML module not checked out")
    monkeypatch.syspath_prepend(str(module_path))
    response = seeded.post(URL, json=REQUEST | {"mode": "local"})
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["is_mock"] is False
    assert result["status"] == "insufficient_data"
    assert result["ml_result"]["data_quality"]["status"] == "partial"
    assert result["anomaly_score"] is None


@pytest.mark.parametrize("example,status,method", [
    ("normal", "normal", "personalized_baseline_deviation"),
    ("anomaly", "anomaly", "personalized_baseline_deviation"),
    ("isolation_normal", "normal", "isolation_forest"),
    ("isolation_anomaly", "anomaly", "isolation_forest"),
])
def test_real_engine_examples_when_available(monkeypatch, example, status, method):
    import json
    from pathlib import Path
    from app.services.ml_adapter import MLAdapter

    pytest.importorskip("sklearn", reason="Optional local ML dependencies not installed")
    module_path = Path(__file__).resolve().parents[2] / "ml-engine"
    fixture = module_path / "examples" / f"{example}.json"
    if not fixture.is_file():
        pytest.skip("Optional sibling ML fixtures unavailable")
    monkeypatch.syspath_prepend(str(module_path))
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    before = copy.deepcopy(payload)
    result = MLAdapter().analyze(payload, [], "local")
    assert payload == before
    assert result.is_mock is False and result.status == status
    assert result.anomaly_detected is (status == "anomaly")
    assert result.ml_result["anomaly"]["method"] == method
    assert result.anomaly_score is not None
