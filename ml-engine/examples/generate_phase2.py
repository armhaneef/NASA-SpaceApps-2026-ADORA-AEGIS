"""Rebuild fixed synthetic Phase 2 JSON fixtures; no random generation."""

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path


def make_record(index, heart_rate=72, spo2=98, temperature=33):
    return {
        "astronaut_id": "SYNTHETIC-ASTRONAUT-001",
        "timestamp": (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=index)).isoformat(),
        "data_source": "synthetic_example",
        "heart_rate": {"value": heart_rate, "unit": "beats/min"},
        "spo2": {"value": spo2, "unit": "%"},
        "temperature": {"value": temperature, "unit": "degC"},
    }


def build_examples():
    normal = make_record(100)
    normal["history"] = [
        make_record(i, 72 + ((i * 7) % 11 - 5) * 0.4,
                    98 + ((i * 3) % 7 - 3) * 0.1,
                    33 + ((i * 5) % 13 - 6) * 0.03)
        for i in range(64)
    ]
    anomaly = deepcopy(normal)
    for name, value in (("heart_rate", 130), ("spo2", 90), ("temperature", 37)):
        anomaly[name]["value"] = value
    trends = make_record(100)
    trends["history"] = [make_record(i * 10, 60 + i * 2, 99 - i * 0.3, 33)
                         for i in range(8)]
    return {"isolation_normal": normal, "isolation_anomaly": anomaly, "trends": trends}


if __name__ == "__main__":
    for name, payload in build_examples().items():
        (Path(__file__).parent / f"{name}.json").write_text(
            json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8",
        )
