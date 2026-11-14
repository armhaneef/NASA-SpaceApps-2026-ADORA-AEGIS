"""Call the public function and validate its wire response without a server."""

import importlib.util
import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from aegis_ml import analyze_health
from aegis_ml.pipeline import analyze_health as implementation

ROOT = Path(__file__).parents[1]
SCHEMA = json.loads((ROOT / "schemas/analysis-output.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def load(name):
    return json.loads((ROOT / "examples" / f"{name}.json").read_text())


def check_response(payload):
    original = deepcopy(payload)
    response = analyze_health(payload)
    assert payload == original
    wire_response = json.loads(json.dumps(response, allow_nan=False))
    VALIDATOR.validate(wire_response)
    assert wire_response["anomaly"]["method"] == wire_response["model"]["name"]
    status = wire_response["anomaly"]["status"]
    assert wire_response["anomaly"]["is_anomaly"] is {
        "normal": False, "anomaly": True, "insufficient_data": None,
    }[status]
    return wire_response


def test_public_import_and_signature():
    assert analyze_health is implementation
    signature = inspect.signature(analyze_health)
    assert list(signature.parameters) == ["payload"]
    assert signature.parameters["payload"].annotation is dict
    assert signature.return_annotation is dict
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("name,status,quality", [
    ("normal", "normal", "valid"), ("anomaly", "anomaly", "valid"),
    ("invalid", "insufficient_data", "partial"),
    ("isolation_normal", "normal", "valid"),
    ("isolation_anomaly", "anomaly", "valid"),
    ("trends", "normal", "valid"),
])
def test_fixtures_obey_complete_wire_contract(name, status, quality):
    response = check_response(load(name))
    assert response["anomaly"]["status"] == status
    assert response["data_quality"]["status"] == quality


def test_no_history_is_not_a_normal_result():
    payload = load("normal")
    payload.pop("history")
    response = check_response(payload)
    assert response["anomaly"]["status"] == "insufficient_data"
    assert response["anomaly"]["normalized_score"] is None
    assert response["data_quality"]["status"] == "valid"


@pytest.mark.parametrize("payload", [None, [], "bad", {}, {"timestamp": "not-a-time"}])
def test_malformed_direct_input_returns_contract(payload):
    response = check_response(payload)
    assert response["data_quality"]["status"] == "invalid"
    assert response["anomaly"]["status"] == "insufficient_data"
    assert response["anomaly"]["normalized_score"] is None


def test_backend_attaches_history_for_one_astronaut():
    fixture = load("isolation_normal")
    current = {key: value for key, value in fixture.items() if key != "history"}
    payload = {**current, "history": fixture["history"]}
    response = check_response(payload)
    assert response["model"]["isolation_forest"]["used"] is True
    foreign = deepcopy(fixture["history"])
    for row in foreign:
        row["astronaut_id"] = "SYNTHETIC-OTHER"
    rejected = check_response({**current, "history": foreign})
    assert rejected["data_quality"]["history_records_accepted"] == 0
    assert rejected["anomaly"]["status"] == "insufficient_data"


def test_schema_detects_missing_fields_and_wrong_units():
    response = analyze_health(load("normal"))
    del response["model"]["isolation_forest"]["fallback_reason"]
    with pytest.raises(ValidationError):
        VALIDATOR.validate(response)
    response = analyze_health(load("normal"))
    response["sensor_readings"]["temperature"]["unit"] = "F"
    with pytest.raises(ValidationError):
        VALIDATOR.validate(response)


def test_optional_fastapi_example_delegates_without_starting_server():
    pytest.importorskip("fastapi", reason="install requirements-integration.txt for the optional example")
    spec = importlib.util.spec_from_file_location("aegis_fastapi_example", ROOT / "examples/fastapi_integration.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = load("normal")
    assert module.analyze_health is analyze_health
    assert module.analyze(payload) == analyze_health(payload)
    assert module.health_check() == {"status": "ok"}
    assert "/ml/analyze" in module.app.openapi()["paths"]
