"""Stateless backend integration entry point; no persistence or model downloads."""

from .baseline import MIN_HISTORY, THRESHOLD, compare
from .isolation import detect
from .trends import analyze_trends
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
    timed_samples = {name: [] for name in SENSORS}
    complete_history = []
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
                    timed_samples[name].append((past_time, past_values[name]["value"]))
            if not past_errors:
                complete_history.append((past_time, [past_values[name]["value"] for name in SENSORS]))
        if past_errors:
            rejected.append({"index": index, "errors": past_errors})
    # Canonical time ordering also makes forest training independent of input order
    # when the history has unique instants. Duplicate policy remains first-wins.
    for name in SENSORS:
        timed_samples[name].sort(key=lambda point: point[0])
        samples[name] = [value for _, value in timed_samples[name]]
    complete_history.sort(key=lambda point: point[0])
    baseline, results = compare(values, samples)
    if not identity_ok:
        for result in results.values():
            result.update(status="insufficient_data", deviation_score=None)
    statuses = [result["status"] for result in results.values()]
    status = "anomaly" if "anomaly" in statuses else (
        "normal" if all(s == "normal" for s in statuses) else "insufficient_data"
    )
    forest_result, forest_metadata = detect(
        values, [row for _, row in complete_history], identity_ok,
    )
    method = "personalized_baseline_deviation"
    scores = [result["deviation_score"] for result in results.values()
              if result["deviation_score"] is not None]
    # An unknown overall status must not be presented as a reassuring numeric score.
    normalized_score = max(scores) / (max(scores) + THRESHOLD) if scores and status != "insufficient_data" else None
    if forest_result is not None:
        status = forest_result["status"]
        normalized_score = forest_result["normalized_score"]
        method = "isolation_forest"
    return {
        "schema_version": "1.0",
        "astronaut_id": record.get("astronaut_id") if isinstance(record.get("astronaut_id"), str) else None,
        "timestamp": record.get("timestamp") if isinstance(record.get("timestamp"), str) else None,
        "data_source": record.get("data_source") if isinstance(record.get("data_source"), str) else None,
        "sensor_readings": values,
        "baseline": baseline,
        "anomaly": {
            "status": status,
            "is_anomaly": True if status == "anomaly" else (False if status == "normal" else None),
            "sensors": results, "method": method, "normalized_score": normalized_score,
            "sensor_method": "personalized_baseline_deviation",
        },
        "trends": analyze_trends(timed_samples),
        "data_quality": {
            "status": "invalid" if not identity_ok else ("partial" if errors or rejected else "valid"),
            "errors": errors, "history_issues": rejected,
            "history_records_received": len(history), "history_records_accepted": accepted,
        },
        "model": {
            "name": method, "version": "2.0.0",
            "minimum_history_per_sensor": MIN_HISTORY, "deviation_threshold": THRESHOLD,
            "synthetic_only": True, "clinically_validated": False,
            "isolation_forest": forest_metadata,
            "score_normalization": "clip(-score_samples, 0, 1)" if forest_result is not None else "max_deviation / (max_deviation + 3)",
        },
    }
