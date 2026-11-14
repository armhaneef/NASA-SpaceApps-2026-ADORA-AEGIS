"""Synthetic behavioral checks, not clinical accuracy evaluation."""

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sklearn.ensemble import IsolationForest

from aegis_ml import analyze_health
from aegis_ml.isolation import CONTAMINATION, RANDOM_STATE
from aegis_ml.validation import SENSORS


def load(name="isolation_normal"):
    return json.loads((Path(__file__).parents[1] / "examples" / f"{name}.json").read_text())


@pytest.mark.parametrize("name,expected", [("isolation_normal", "normal"), ("isolation_anomaly", "anomaly")])
def test_forest_examples(name, expected):
    payload = load(name)
    result = analyze_health(payload)
    assert result["model"]["name"] == "isolation_forest"
    assert result["model"]["isolation_forest"]["used"] is True
    assert result["anomaly"]["status"] == expected
    assert 0 <= result["anomaly"]["normalized_score"] <= 1
    json.dumps(result, allow_nan=False)


def test_score_orientation_and_exact_sklearn_normalization():
    payload = load()
    matrix = [[row[name]["value"] for name in SENSORS] for row in payload["history"]]
    current = [[payload[name]["value"] for name in SENSORS]]
    model = IsolationForest(n_estimators=100, max_samples="auto", contamination=CONTAMINATION,
                            random_state=RANDOM_STATE, n_jobs=1).fit(matrix)
    result = analyze_health(payload)
    assert result["anomaly"]["normalized_score"] == pytest.approx(-float(model.score_samples(current)[0]))
    assert result["model"]["isolation_forest"]["score_threshold"] == pytest.approx(-float(model.offset_))
    assert analyze_health(load("isolation_anomaly"))["anomaly"]["normalized_score"] > result["anomaly"]["normalized_score"]


def test_determinism_ordering_and_input_immutability():
    payload = load()
    original = deepcopy(payload)
    first = analyze_health(payload)
    assert payload == original
    assert analyze_health(payload) == first
    payload["history"].reverse()
    assert analyze_health(payload) == first


@pytest.mark.parametrize("count,method", [(31, "personalized_baseline_deviation"), (32, "isolation_forest")])
def test_minimum_training_boundary(count, method):
    payload = load()
    payload["history"] = payload["history"][:count]
    result = analyze_health(payload)
    assert result["model"]["name"] == method
    assert result["model"]["isolation_forest"]["training_records"] == count


@pytest.mark.parametrize("mode", ["foreign", "future", "duplicate", "unit", "nan", "provenance", "bad_timestamp"])
def test_forest_training_excludes_ineligible_rows(mode):
    payload = load()
    payload["history"] = payload["history"][:32]
    row = payload["history"][0]
    if mode == "foreign":
        row["astronaut_id"] = "SYNTHETIC-OTHER"
    elif mode == "future":
        row["timestamp"] = payload["timestamp"]
    elif mode == "duplicate":
        row["timestamp"] = payload["history"][1]["timestamp"]
    elif mode == "unit":
        row["spo2"]["unit"] = "wrong"
    elif mode == "nan":
        row["spo2"]["value"] = float("nan")
    elif mode == "provenance":
        row["data_source"] = "real"
    else:
        row["timestamp"] = "bad"
    result = analyze_health(payload)
    assert result["model"]["name"] == "personalized_baseline_deviation"
    assert result["model"]["isolation_forest"]["training_records"] == 31
    assert result["data_quality"]["status"] == "partial"
    json.dumps(result, allow_nan=False)


def test_constant_history_fallback():
    payload = load("isolation_anomaly")
    for row in payload["history"]:
        for name, value in (("heart_rate", 72), ("spo2", 98), ("temperature", 33)):
            row[name]["value"] = value
    result = analyze_health(payload)
    assert result["model"]["isolation_forest"]["fallback_reason"] == "constant_history"
    assert result["anomaly"]["status"] == "anomaly"


def test_partial_current_falls_back_without_imputation():
    payload = load("isolation_anomaly")
    payload.pop("spo2")
    result = analyze_health(payload)
    assert result["model"]["isolation_forest"]["fallback_reason"] == "incomplete_current_sensors"
    assert result["sensor_readings"]["spo2"]["value"] is None
    assert result["anomaly"]["status"] == "anomaly"
    assert result["anomaly"]["normalized_score"] > 0.5


def test_invalid_identity_does_not_train_or_infer_trends():
    payload = load()
    payload["astronaut_id"] = None
    result = analyze_health(payload)
    assert result["model"]["isolation_forest"]["training_records"] == 0
    assert result["anomaly"]["normalized_score"] is None
    assert all(row["direction"] == "unknown" for row in result["trends"].values())


def test_fallback_score_normalization_and_unknown():
    payload = load("anomaly")
    result = analyze_health(payload)
    score = max(row["deviation_score"] for row in result["anomaly"]["sensors"].values())
    assert result["anomaly"]["normalized_score"] == score / (score + 3)
    payload["history"] = []
    assert analyze_health(payload)["anomaly"]["normalized_score"] is None


def test_trend_fixture_directions_and_units():
    trends = analyze_health(load("trends"))["trends"]
    assert trends["heart_rate"]["direction"] == "increasing"
    assert trends["spo2"]["direction"] == "decreasing"
    assert trends["temperature"]["direction"] == "stable"
    assert trends["heart_rate"]["slope_per_hour"] == pytest.approx(12)
    assert trends["spo2"]["slope_per_hour"] == pytest.approx(-1.8)
    assert trends["temperature"]["unit"] == "degC/hour"


def test_irregular_time_order_uses_elapsed_hours_and_ignores_current():
    payload = load("normal")
    origin = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for row, hour in zip(payload["history"], [0, 1, 3]):
        row["timestamp"] = (origin + timedelta(hours=hour)).isoformat()
        row["heart_rate"]["value"] = 60 + 2 * hour
    payload["history"].reverse()
    payload["heart_rate"]["value"] = 200
    trend = analyze_health(payload)["trends"]["heart_rate"]
    assert trend["slope_per_hour"] == pytest.approx(2)
    assert trend["fitted_change"] == pytest.approx(6)
    assert trend["direction"] == "increasing"


@pytest.mark.parametrize("mode", ["missing", "invalid", "foreign", "duplicate"])
def test_trends_insufficient_valid_sensor_history(mode):
    payload = load("normal")
    row = payload["history"][0]
    if mode == "missing":
        row.pop("heart_rate")
    elif mode == "invalid":
        row["heart_rate"]["value"] = "bad"
    elif mode == "foreign":
        row["astronaut_id"] = "SYNTHETIC-OTHER"
    else:
        row["timestamp"] = payload["history"][1]["timestamp"]
    trend = analyze_health(payload)["trends"]["heart_rate"]
    assert trend["count"] == 2
    assert trend["direction"] == "unknown"
    assert trend["slope_per_hour"] is None


@pytest.mark.parametrize("name", ["normal", "invalid", "isolation_normal", "isolation_anomaly"])
def test_existing_output_keys_types_units_and_statuses(name):
    result = analyze_health(load(name))
    assert result["schema_version"] == "1.0"
    assert {"astronaut_id", "timestamp", "data_source", "sensor_readings", "baseline", "anomaly", "data_quality", "model"} <= result.keys()
    assert {"status", "is_anomaly", "sensors"} <= result["anomaly"].keys()
    assert result["anomaly"]["status"] in {"normal", "anomaly", "insufficient_data"}
    for sensor, (unit, *_rest) in SENSORS.items():
        assert result["sensor_readings"][sensor]["unit"] == unit
        assert {"status", "deviation_score"} <= result["anomaly"]["sensors"][sensor].keys()
    assert result["anomaly"]["sensor_method"] == "personalized_baseline_deviation"
    json.dumps(result, allow_nan=False)
