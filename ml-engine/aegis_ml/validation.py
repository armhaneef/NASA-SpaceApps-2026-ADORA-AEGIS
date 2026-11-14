"""Input checks; ranges are prototype sensor bounds, not clinical thresholds."""

from datetime import datetime
from math import isfinite

# name: (unit, minimum, maximum, minimum deviation scale)
SENSORS = {
    "heart_rate": ("beats/min", 20, 250, 5.0),
    "spo2": ("%", 0, 100, 1.0),
    "temperature": ("degC", 10, 50, 0.5),
}


def parse_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.utcoffset() is not None else None
    except (ValueError, OverflowError):
        return None


def validate_record(record):
    """Return sanitized sensors and field errors without imputing values."""
    values, errors = {}, {}
    if not isinstance(record, dict):
        record = {}
    identifier = record.get("astronaut_id")
    if not isinstance(identifier, str) or not identifier.strip():
        errors["astronaut_id"] = "expected nonempty string"
    if parse_timestamp(record.get("timestamp")) is None:
        errors["timestamp"] = "expected ISO 8601 timestamp with timezone"
    source = record.get("data_source")
    if not isinstance(source, str) or not source.startswith("synthetic"):
        errors["data_source"] = "expected explicit synthetic provenance"
    for name, (unit, low, high, _) in SENSORS.items():
        reading = record.get(name)
        value = reading.get("value") if isinstance(reading, dict) else None
        reason = None
        if reading is None or (isinstance(reading, dict) and value is None):
            reason = "missing reading"
        elif not isinstance(reading, dict) or reading.get("unit") != unit:
            reason = f"expected measurement object with unit {unit}"
        elif isinstance(value, bool) or not isinstance(value, (int, float)):
            reason = "expected finite numeric value"
        else:
            try:
                if not isfinite(value) or not low <= value <= high:
                    reason = f"expected finite value in [{low}, {high}]"
            except (OverflowError, ValueError):
                reason = "expected finite numeric value"
        if reason:
            errors[name] = reason
        values[name] = {"value": None if reason else float(value), "unit": unit}
    return values, errors
