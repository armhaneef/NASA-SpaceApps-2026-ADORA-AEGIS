"""Stateless backend integration entry point; no persistence or model downloads."""

from .baseline import MIN_HISTORY, THRESHOLD, compare
from .validation import SENSORS, parse_timestamp, validate_record


def analyze_health(payload: dict) -> dict:
    """Analyze a current shared-schema record with an optional history list."""
    is_object = isinstance(payload, dict)
    record = payload if is_object else {}
    values, errors = validate_record(record)
    if not is_object:
        errors["payload"] = "expected object"
    history = record.get("history", [])
    if not isinstance(history, list):
        errors["history"] = "expected list"
        history = []
    samples = {name: [] for name in SENSORS}
    rejected = []
    accepted = 0
    seen = set()
    current_time = parse_timestamp(record.get("timestamp"))
    identity_ok = not any(key in errors for key in ("astronaut_id", "timestamp", "data_source", "payload"))
    for index, item in enumerate(history):
        past_values, past_errors = validate_record(item)
        past_time = parse_timestamp(item.get("timestamp")) if isinstance(item, dict) else None
        if not identity_ok:
            past_errors["record"] = "current record identity, timestamp or provenance invalid"
        elif not isinstance(item, dict) or item.get("astronaut_id") != record.get("astronaut_id"):
            past_errors["astronaut_id"] = "different astronaut"
        elif past_time is not None and past_time >= current_time:
            past_errors["timestamp"] = "history must precede current reading"
        elif past_time in seen:
            past_errors["timestamp"] = "duplicate historical timestamp"
        metadata_invalid = any(key not in SENSORS for key in past_errors)
        if not metadata_invalid:
            seen.add(past_time)
            accepted += 1
            for name in SENSORS:
                if name not in past_errors:
                    samples[name].append(past_values[name]["value"])
        if past_errors:
            rejected.append({"index": index, "errors": past_errors})
    baseline, results = compare(values, samples)
    if not identity_ok:
        for result in results.values():
            result.update(status="insufficient_data", deviation_score=None)
    statuses = [result["status"] for result in results.values()]
    status = "anomaly" if "anomaly" in statuses else (
        "normal" if all(s == "normal" for s in statuses) else "insufficient_data"
    )
    return {
        "schema_version": "1.0",
        "astronaut_id": record.get("astronaut_id") if isinstance(record.get("astronaut_id"), str) else None,
        "timestamp": record.get("timestamp") if isinstance(record.get("timestamp"), str) else None,
        "data_source": record.get("data_source") if isinstance(record.get("data_source"), str) else None,
        "sensor_readings": values,
        "baseline": baseline,
        "anomaly": {"status": status, "is_anomaly": True if status == "anomaly" else (False if status == "normal" else None), "sensors": results},
        "data_quality": {
            "status": "invalid" if not identity_ok else ("partial" if errors or rejected else "valid"),
            "errors": errors, "history_issues": rejected,
            "history_records_received": len(history), "history_records_accepted": accepted,
        },
        "model": {
            "name": "personalized_baseline_deviation", "version": "1.0.0",
            "minimum_history_per_sensor": MIN_HISTORY, "deviation_threshold": THRESHOLD,
            "synthetic_only": True, "clinically_validated": False,
        },
    }
