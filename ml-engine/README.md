# AEGIS ML engine — Phase 1

Working personalized baseline detector for **synthetic data only**. This is not
a clinically validated system and must not support medical or mission decisions.
Isolation Forest, trend prediction, persistence and HTTP endpoints are not implemented.

## Run and integrate

From the repository root with Python 3.10+:

```powershell
py -m pip install -r ml-engine/requirements.txt
py -m pytest ml-engine/tests -v
$env:PYTHONPATH = (Resolve-Path ml-engine).Path
py -c "import json; from aegis_ml import analyze_health; print(json.dumps(analyze_health(json.load(open('ml-engine/examples/normal.json'))), indent=2, allow_nan=False))"
```

Backend callers add `ml-engine/` to the Python import path and use
`from aegis_ml import analyze_health`, then call `analyze_health(payload)`.
Runtime uses only the standard library; pytest is the test dependency.
The function is stateless and performs no I/O or network requests.

## Input contract

The payload is the current record using the repository's
[shared schema](../docs/data-schema.md), extended locally with optional `history`,
a list of records of the same shape. No shared API endpoints are changed.
Metadata requires nonempty `astronaut_id`, timezone-aware ISO 8601 `timestamp`,
and a `data_source` beginning with `synthetic` (a declaration, not proof of origin).
Measurements require numeric `value` and exact `unit`:

| Field | Unit | Inclusive input bounds | Minimum deviation scale |
| --- | --- | --- | --- |
| `heart_rate` | `beats/min` | 20–250 | 5 |
| `spo2` | `%` | 0–100 | 1 |
| `temperature` | `degC` | 10–50 | 0.5 |

`temperature` represents skin temperature in this module. Bounds and scale floors
are illustrative engineering choices, not clinical thresholds. Other shared fields
such as `co2` and `respiration_rate` are ignored in Phase 1. Missing values, booleans,
numeric strings, nonfinite numbers, wrong units and out-of-bounds values become null
with explicit quality errors; there is no imputation.

## Baseline method

Only earlier records for the same astronaut with valid metadata and synthetic
provenance contribute. Duplicate instants are excluded, with the first eligible
record winning. Sensor errors exclude that sensor while preserving other valid
measurements. Each sensor needs at least three valid historical values.
Its baseline uses the mean and population standard deviation of eligible history;
the current record never contributes.

`deviation_score = abs(current - mean) / max(std, minimum_scale)`

A score **strictly greater than 3** is unusual. Floors handle constant history.
This is a deterministic deviation heuristic, not a trained predictive model.
Supply curated baseline history: historical anomalies can distort the baseline.
There is no recency window, activity adjustment or contamination removal.

## Output contract (schema_version 1.0)

- `astronaut_id`, `timestamp`, `data_source`: input metadata; non-string values become null.
- `sensor_readings`: sanitized, unit-bearing values.
- `baseline`: per-sensor `count`, `mean`, `std`, effective `scale`, `unit`, `ready`.
- `anomaly`: overall `status`, nullable `is_anomaly`, and per-sensor status and deviation scores.
- `data_quality`: status, current-field errors, indexed history issues and received/accepted record counts.
- `model`: method name, version, minimum history, threshold and prototype labels.

Overall status is `anomaly` if any evaluable sensor is unusual, `normal` only
when all three are evaluable and normal, otherwise `insufficient_data`.
`is_anomaly` is null for insufficient data. Invalid current identity, timestamp
or provenance prevents comparison. Quality is `invalid` for invalid current
metadata, `partial` for sensor/history errors, otherwise `valid`. Valid input can
still have insufficient history. Accepted history counts refer to metadata-eligible
records; per-sensor counts report usable values. Output supports strict JSON.

## Examples and layout

`examples/normal.json`, `examples/anomaly.json` and `examples/invalid.json` are
fixed synthetic fixtures with expected statuses `normal`, `anomaly` and
`insufficient_data` respectively. The invalid example has partial data quality.

`aegis_ml/validation.py` validates inputs, `baseline.py` calculates baselines and
scores, and `pipeline.py` exposes `analyze_health`. The existing `models/`,
`preprocessing/` and `evaluation/` folders remain available for later experiments.
Tests cover examples, personalization, malformed inputs, history filtering,
constant history, threshold boundaries, partial data and repeatability.
