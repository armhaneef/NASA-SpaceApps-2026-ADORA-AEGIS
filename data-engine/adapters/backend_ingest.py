"""Convert generator output to the existing backend contract and optionally send it.

Only measurements whose meanings are explicit in the source field names are
converted. ``body_temperature_c`` is deliberately omitted because its skin/core
semantics have not been agreed. The distinct ``skin_temperature_c`` field is a
synthetic software fixture and is never derived from body temperature.
"""

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MEASUREMENT_FIELDS = {
    "heart_rate_bpm": ("heart_rate", "bpm"),
    "spo2_percent": ("spo2", "%"),
    "skin_temperature_c": ("skin_temperature", "degC"),
    "respiration_rate_bpm": ("respiration_rate", "breaths/min"),
}
DATA_SOURCE = "synthetic_data_engine"


@dataclass(frozen=True)
class IngestSummary:
    batches_with_new_measurements: int
    fully_reused_batches: int


def to_backend_payload(record: dict[str, Any]) -> dict[str, Any]:
    """Map one flat generator record to the backend's grouped ingestion schema."""
    astronaut_id = record.get("astronaut_id")
    timestamp = record.get("timestamp")
    if not isinstance(astronaut_id, str) or not astronaut_id.strip():
        raise ValueError("astronaut_id must be a non-empty string")
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("timestamp must be a non-empty ISO 8601 string")

    payload: dict[str, Any] = {
        "astronaut_id": astronaut_id,
        "timestamp": timestamp,
        "sensor_type": "synthetic_multi_sensor",
        "data_source": DATA_SOURCE,
        "is_simulated": True,
        "quality": "synthetic_demo",
    }
    for source_field, (measurement_type, unit) in MEASUREMENT_FIELDS.items():
        if source_field not in record:
            continue
        value = record[source_field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{source_field} must be a finite number")
        payload[measurement_type] = {"value": value, "unit": unit}

    if not any(key in payload for key, _ in MEASUREMENT_FIELDS.values()):
        raise ValueError("record contains no measurements supported by the backend adapter")
    return payload


def _request_json(base_url: str, path: str, method: str = "GET", body: dict | None = None):
    data = None if body is None else json.dumps(body, allow_nan=False).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}{path}", data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            content = response.read()
            return response.status, json.loads(content) if content else None
    except HTTPError as error:
        content = error.read()
        return error.code, json.loads(content) if content else None
    except (TimeoutError, URLError) as error:
        raise RuntimeError(f"Backend request failed for {path}: {error}") from error


def ensure_astronaut(base_url: str, astronaut_id: str) -> None:
    """Create the fabricated profile when it does not already exist."""
    status, _ = _request_json(base_url, f"/astronauts/{astronaut_id}")
    if status == 200:
        return
    if status != 404:
        raise RuntimeError(f"Could not check astronaut profile (HTTP {status})")

    status, _ = _request_json(base_url, "/astronauts", "POST", {
        "astronaut_id": astronaut_id,
        "name": "Synthetic Demonstration Astronaut",
        "mission_id": "AEGIS-DEMO",
        "mission_role": "synthetic software demonstration",
        "profile_metadata": {"data_source": DATA_SOURCE, "is_simulated": True},
    })
    if status != 201:
        raise RuntimeError(f"Could not create synthetic astronaut profile (HTTP {status})")


def ingest_records(base_url: str, records: list[dict[str, Any]]) -> IngestSummary:
    """Create the synthetic profile and post records using the documented API."""
    if not records:
        raise ValueError("at least one synthetic reading is required")
    astronaut_id = records[0].get("astronaut_id")
    if not isinstance(astronaut_id, str) or not astronaut_id.strip():
        raise ValueError("records need a valid astronaut_id")
    ensure_astronaut(base_url, astronaut_id)

    batches_with_new_measurements = 0
    fully_reused_batches = 0
    for record in records:
        payload = to_backend_payload(record)
        if payload["astronaut_id"] != astronaut_id:
            raise ValueError("all records must belong to the same synthetic astronaut")
        status, response = _request_json(base_url, "/health/ingest", "POST", payload)
        if status not in (200, 201):
            raise RuntimeError(f"Backend rejected a synthetic reading (HTTP {status}): {response}")
        if status == 201:
            # HTTP 201 means this grouped request created at least one row;
            # the response also includes any exact matches reused in the same
            # batch, so it cannot provide a measurement-level insertion count.
            batches_with_new_measurements += 1
        else:
            fully_reused_batches += 1
    return IngestSummary(batches_with_new_measurements, fully_reused_batches)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send generated synthetic readings to the local AEGIS API.")
    parser.add_argument("--api-base-url", default=os.getenv("AEGIS_API_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--readings", type=int, default=60)
    parser.add_argument("--scenario", choices=("normal", "warning", "critical"), default="normal")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--astronaut-id", default="AST-001")
    args = parser.parse_args()

    generator_path = os.path.join(os.path.dirname(__file__), "..", "generators")
    sys.path.insert(0, os.path.abspath(generator_path))
    from generate_synthetic_data import generate_readings

    records = generate_readings(args.readings, args.scenario, args.seed, args.astronaut_id)
    summary = ingest_records(args.api_base_url, records)
    print(f"Processed synthetic readings for {records[0]['astronaut_id']}.")
    print(f"Reading batches with at least one newly stored measurement: "
          f"{summary.batches_with_new_measurements}; "
          f"fully reused reading batches: {summary.fully_reused_batches}.")
    print("body_temperature_c was omitted; separate skin_temperature_c was mapped explicitly.")


if __name__ == "__main__":
    main()
