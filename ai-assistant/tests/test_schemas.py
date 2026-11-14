from app.schemas.alert import MLInputRecord


def test_valid_mock_record_passes():
    payload = {
        "astronaut_id": "AST-001",
        "timestamp": "2026-11-14T07:00:00Z",
        "metric": "heart_rate",
        "current_value": 110,
        "baseline_value": 72,
        "unit": "bpm",
        "anomaly_detected": True,
        "anomaly_score": 0.87,
        "score_definition": "example_score_not_medical_probability",
        "trend": "increasing",
        "sensor_quality": "good",
        "data_source": "simulated",
        "model_name": "isolation_forest",
        "context": {"activity": "unknown"},
    }
    record = MLInputRecord.model_validate(payload)
    assert record.astronaut_id == "AST-001"
    assert record.metric == "heart_rate"
    assert record.unit == "bpm"
    assert record.baseline_status == "above baseline"


def test_invalid_metric_fails():
    payload = {
        "astronaut_id": "AST-001",
        "timestamp": "2026-11-14T07:00:00Z",
        "metric": "unknown_metric",
        "current_value": 40,
        "baseline_value": 50,
        "unit": "bpm",
    }
    try:
        MLInputRecord.model_validate(payload)
        assert False, "Expected validation to fail"
    except ValueError:
        pass


def test_invalid_unit_fails_for_metric():
    payload = {
        "astronaut_id": "AST-001",
        "timestamp": "2026-11-14T07:00:00Z",
        "metric": "heart_rate",
        "current_value": 90,
        "baseline_value": 72,
        "unit": "C",
    }
    try:
        MLInputRecord.model_validate(payload)
        assert False, "Expected validation to fail"
    except ValueError:
        pass
