import json
from copy import deepcopy
from pathlib import Path

import pytest

from aegis_ml import analyze_health


def fixture(name="normal"):
    return json.loads((Path(__file__).parents[1] / "examples" / f"{name}.json").read_text())


@pytest.mark.parametrize("name,status", [("normal", "normal"), ("anomaly", "anomaly"), ("invalid", "insufficient_data")])
def test_examples(name, status):
    result = analyze_health(fixture(name))
    assert result["anomaly"]["status"] == status
    json.dumps(result, allow_nan=False)


def test_personalized_baseline_and_no_mutation():
    payload = fixture()
    original = deepcopy(payload)
    result = analyze_health(payload)
    assert payload == original
    assert result["baseline"]["heart_rate"]["mean"] == 72
    assert result["baseline"]["heart_rate"]["count"] == 3
    assert result["data_quality"]["status"] == "valid"
    for row in payload["history"]:
        row["heart_rate"]["value"] += 40
    assert analyze_health(payload)["anomaly"]["status"] == "anomaly"


@pytest.mark.parametrize("value", [None, True, "72", float("nan"), float("inf"), -1, 251, 10**1000])
def test_invalid_numbers(value):
    payload = fixture()
    payload["heart_rate"]["value"] = value
    result = analyze_health(payload)
    assert result["sensor_readings"]["heart_rate"]["value"] is None
    assert "heart_rate" in result["data_quality"]["errors"]
    assert result["anomaly"]["is_anomaly"] is None
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("payload", [None, [], {}, "invalid"])
def test_malformed_payload(payload):
    result = analyze_health(payload)
    assert result["data_quality"]["status"] == "invalid"
    assert result["anomaly"]["is_anomaly"] is None


@pytest.mark.parametrize("field,value", [("astronaut_id", ""), ("timestamp", "2026-01-01"), ("timestamp", "bad"), ("data_source", "real")])
def test_invalid_metadata(field, value):
    payload = fixture()
    payload[field] = value
    result = analyze_health(payload)
    assert result["data_quality"]["status"] == "invalid"
    assert result["anomaly"]["status"] == "insufficient_data"


@pytest.mark.parametrize("history", [[], None, {}, [None], [42]])
def test_bad_or_missing_history(history):
    payload = fixture()
    payload["history"] = history
    assert analyze_health(payload)["anomaly"]["is_anomaly"] is None


@pytest.mark.parametrize("change", ["other_astronaut", "future", "duplicate", "unit", "provenance"])
def test_history_filtering(change):
    payload = fixture()
    row = payload["history"][0]
    if change == "other_astronaut":
        row["astronaut_id"] = "SYNTHETIC-OTHER"
    elif change == "future":
        row["timestamp"] = payload["timestamp"]
    elif change == "duplicate":
        row["timestamp"] = payload["history"][1]["timestamp"]
    elif change == "unit":
        row["heart_rate"]["unit"] = "Hz"
    else:
        row["data_source"] = "unknown"
    result = analyze_health(payload)
    assert result["baseline"]["heart_rate"]["count"] == 2
    assert result["anomaly"]["status"] == "insufficient_data"
    assert result["data_quality"]["history_issues"]


def test_constant_history_and_threshold():
    payload = fixture()
    for row in payload["history"]:
        row["heart_rate"]["value"] = 72
    payload["heart_rate"]["value"] = 87
    assert analyze_health(payload)["anomaly"]["status"] == "normal"
    payload["heart_rate"]["value"] = 88
    assert analyze_health(payload)["anomaly"]["status"] == "anomaly"


def test_partial_data_still_reports_detected_anomaly():
    payload = fixture("anomaly")
    payload.pop("spo2")
    result = analyze_health(payload)
    assert result["anomaly"]["is_anomaly"] is True
    assert result["data_quality"]["status"] == "partial"


def test_timezone_equivalent_duplicates():
    payload = fixture()
    payload["history"][1]["timestamp"] = "2026-01-01T01:00:00+01:00"
    assert analyze_health(payload)["baseline"]["heart_rate"]["count"] == 2


def test_stateless_repeatability():
    payload = fixture()
    assert analyze_health(payload) == analyze_health(payload)
    payload.pop("history")
    assert analyze_health(payload)["anomaly"]["is_anomaly"] is None
