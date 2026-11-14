from app.schemas.alert import MLInputRecord
from app.services.alert_explainer import AlertExplainer


def test_explainer_reports_review_for_anomaly():
    record = MLInputRecord.model_validate({
        "astronaut_id": "AST-001",
        "timestamp": "2026-11-14T07:00:00Z",
        "metric": "heart_rate",
        "current_value": 110,
        "baseline_value": 72,
        "unit": "bpm",
        "anomaly_detected": True,
        "trend": "increasing",
        "sensor_quality": "good",
        "data_source": "simulated",
    })
    result = AlertExplainer.explain(record)
    assert result.status == "review"
    assert "heart rate" in result.explanation.lower()
    assert result.medical_diagnosis is False
    assert result.data_source == "simulated"


def test_explainer_handles_missing_baseline():
    record = MLInputRecord.model_validate({
        "astronaut_id": "AST-001",
        "timestamp": "2026-11-14T07:00:00Z",
        "metric": "sleep_duration",
        "current_value": 6,
        "unit": "hours",
        "anomaly_detected": False,
        "trend": "unknown",
        "sensor_quality": "fair",
        "data_source": "simulated",
    })
    result = AlertExplainer.explain(record)
    assert "baseline" in result.explanation.lower()
    assert result.status == "review"
