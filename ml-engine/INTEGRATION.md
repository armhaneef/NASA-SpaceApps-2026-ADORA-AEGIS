# Member 4: FastAPI integration handoff

The ML module is ready to call in-process. The existing backend has only
`GET /health`; the route below is a standalone example, not an existing team API.
No backend or shared documentation files were modified. Agree on a shared route
with its owner before adopting it. All data and examples are synthetic; outputs
are not clinical diagnoses, medical probabilities or validated health predictions.

## 1. Install and confirm the exact import

Run from the repository root in the backend's Python environment (Python 3.11+):

```powershell
py -m pip install -r ml-engine/requirements-integration.txt
$env:PYTHONPATH = (Resolve-Path ml-engine).Path
py -c "import inspect; from aegis_ml import analyze_health; print(inspect.signature(analyze_health))"
```

Expected signature: `(payload: dict) -> dict`.

```python
from aegis_ml import analyze_health

result = analyze_health(payload)
```

The implementation is `aegis_ml.pipeline.analyze_health`, re-exported by
`aegis_ml/__init__.py`. `ml-engine` is a filesystem directory, not a Python module
name: do not use `import ml-engine`. Keep `ml-engine/` on `PYTHONPATH` in the
backend process/container. Its location is independent of Uvicorn's `--app-dir`.
The function is synchronous, stateless, leaves its input unchanged, and performs
no database, filesystem or network I/O. It fits a model in memory on each eligible
call; scikit-learn is required even when the baseline fallback is selected.

For just ML and its tests, install `requirements.txt`; the integration requirements
add FastAPI and Uvicorn using the same version bounds as the backend.

## 2. Run the standalone FastAPI example

[examples/fastapi_integration.py](examples/fastapi_integration.py) provides a tagged
health route and a synchronous ML route, matching the backend's style:

```powershell
$env:PYTHONPATH = (Resolve-Path ml-engine).Path
py -m uvicorn fastapi_integration:app --app-dir ml-engine/examples --port 8001
```

In another PowerShell terminal, from the repository root:

```powershell
$body = Get-Content ml-engine/examples/isolation_normal.json -Raw
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/ml/analyze -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 20
```

The small route Member 4 can adapt in their own backend work is:

```python
from typing import Annotated
from fastapi import Body
from aegis_ml import analyze_health

# `app` is the existing FastAPI application.
@app.post("/ml/analyze", tags=["ml"])
def analyze(payload: Annotated[dict, Body()]) -> dict:
    return analyze_health(payload)
```

The route returns the full result unchanged. It uses ordinary `def` so FastAPI
runs model work in its thread pool ([FastAPI concurrency documentation](https://fastapi.tiangolo.com/async/)).
If integrating into an existing asynchronous handler, use
`await starlette.concurrency.run_in_threadpool(analyze_health, payload)` rather
than calling model fitting directly on the event loop. This is not a throughput
benchmark; history size, request limits and any production worker strategy belong
to the backend owner. No response filtering model should discard the quality,
method, baseline or trend fields, or strip null values.

## 3. Required input and sensor units

The payload is the **current record at the top level**, with optional `history`:

```json
{
  "astronaut_id": "SYNTHETIC-ASTRONAUT-001",
  "timestamp": "2026-01-01T04:00:00Z",
  "data_source": "synthetic_example",
  "heart_rate": {"value": 72, "unit": "beats/min"},
  "spo2": {"value": 98, "unit": "%"},
  "temperature": {"value": 33, "unit": "degC"},
  "history": []
}
```

This valid example deliberately returns `insufficient_data` because its history
is empty. See `examples/normal.json` for the same shape with usable history.

| Field | Required for full analysis | Validation |
| --- | --- | --- |
| `astronaut_id` | Yes | Nonempty string; exact identifier matching in history |
| `timestamp` | Yes | ISO 8601 string with timezone, preferably UTC `Z` |
| `data_source` | Yes | String starting with `synthetic`; a declaration, not proof of origin |
| `heart_rate` | Yes | Numeric finite value, inclusive 20–250, exact unit `beats/min` |
| `spo2` | Yes | Numeric finite value, inclusive 0–100, exact unit `%` |
| `temperature` | Yes | Skin temperature, numeric finite value, inclusive 10–50, exact unit `degC` |
| `history` | No | List of historical records with the same metadata and measurement shape; defaults to `[]` |

Bounds are prototype input checks, not clinical thresholds. Booleans, numeric
strings, wrong units, missing/null values, infinities and NaN are not accepted
sensor readings. Invalid sensor values become null with quality errors; there is
no conversion or imputation. Use standard JSON (which has no NaN or Infinity).
`skin_temperature`, `heartRate` and `SpO2` are not field aliases. Shared-schema
`respiration_rate`, `co2` and other extra fields are ignored, not analyzed or echoed.
Datetimes and database numeric types must be converted to ordinary JSON strings
and finite Python int/float values before calling the function.

## 4. Attach astronaut-specific history in the backend

ML does not look up, store or retain readings. The backend supplies history on
**every call**, before inserting the current reading into that historical set.
Use the same synthetic astronaut ID and only records earlier than the current
timestamp. Each history record must include its own ID, timestamp, provenance
and unit-bearing measurements. Nested `history` fields have no effect.

```python
# `current_record` is the current shared-schema dict.
# `historical_records` is a list retrieved by your own data layer using
# astronaut_id == current_record["astronaut_id"] and timestamp < current timestamp.
payload = {**current_record, "history": historical_records}
result = analyze_health(payload)
```

Do not concatenate histories across astronauts or replace real provenance with a
synthetic label. Select only synthetic fixtures in this prototype. ML repeats ID,
timestamp and provenance checks, rejects current/future rows, and excludes
duplicate instants (including equivalent timezone offsets): the first eligible
record wins. Order is otherwise normalized by timestamp. Metadata-invalid rows
are excluded entirely; a sensor-invalid historical row can still contribute its
other sensors to baseline/trends but cannot train the joint forest.

- Baseline needs at least 3 valid historical measurements **per sensor**.
- Isolation Forest needs at least 32 complete eligible records, at least two
  distinct feature vectors, valid current metadata and all three current sensors.
  Otherwise baseline fallback is explicit in model metadata.
- Trends need at least 3 valid unique historical instants per sensor. They use
  actual elapsed time and exclude the current reading. They describe history;
  they do not predict future measurements.

The module uses the full supplied history with no recency window or automatic
outlier removal. The backend should choose a curated, bounded history window
appropriate to the synthetic demo and preserve that policy across requests.

## 5. Complete output schema and interpretation

The machine-readable [analysis-output.schema.json](schemas/analysis-output.schema.json)
is JSON Schema Draft 2020-12. It covers **every current response field**, types,
nullable values, required keys, status/method enums and exact sensor units.
All current keys are required; extra fields are allowed for additive compatibility.
No external schema fetch is needed to validate it. The schema describes response
structure; cross-field semantics are checked in contract tests and explained here.

| Path | Complete contents / meaning |
| --- | --- |
| `schema_version` | String `1.0`; Phase 2 fields are additive |
| `astronaut_id`, `timestamp`, `data_source` | Original strings or null for non-string inputs; invalid strings remain visible with quality errors |
| `sensor_readings.{sensor}` | `value`: number/null; `unit`: exact sensor unit |
| `baseline.{sensor}` | `count`: nonnegative integer; `mean`, `std`, `scale`: number/null; `unit`: sensor unit; `ready`: boolean |
| `anomaly` | `status`: normal/anomaly/insufficient_data; `is_anomaly`: false/true/null respectively; `sensors`, `method`, `normalized_score`, `sensor_method` |
| `anomaly.sensors.{sensor}` | `status` using the same three strings; nonnegative `deviation_score` or null |
| `anomaly.method` | `isolation_forest` or `personalized_baseline_deviation`; identifies the overall detector |
| `anomaly.sensor_method` | Always `personalized_baseline_deviation`; sensor results are baseline explanations, not forest attributions, and may disagree with the joint result |
| `anomaly.normalized_score` | Number in [0,1], or null when overall result is insufficient; larger means more unusual, not a medical probability |
| `trends.{sensor}` | `direction`: increasing/decreasing/stable/unknown; `count`: integer; `slope_per_hour`, `fitted_change`: number/null; `unit`: sensor unit + `/hour`; positive `change_threshold`; `start_timestamp`, `end_timestamp`: string/null |
| `data_quality` | `status`: valid/partial/invalid; `errors`: field-to-message object; `history_issues`: list of `{index, errors}`; `history_records_received`, `history_records_accepted`: nonnegative integers |
| `model` | `name`: active detector; `version`: `2.0.0`; `minimum_history_per_sensor`: 3; `deviation_threshold`: 3; `synthetic_only`: true; `clinically_validated`: false; `isolation_forest`; `score_normalization` |
| `model.isolation_forest` | `minimum_history`: 32; `training_records`: complete eligible count (even when training skipped); `features`: ordered sensor-name list; `random_state`: 42; `n_estimators`: 100; `contamination`: 0.05; `sklearn_version`: string; `used`: boolean; `fallback_reason`: string/null; `score_threshold`: number/null |

`{sensor}` always means exactly `heart_rate`, `spo2`, `temperature`. Baseline
`std` is population standard deviation; `scale` is max(std, floor), with floors
5, 1 and 0.5 respectively. Baseline statistics stay null until its count reaches 3.
Accepted-history count refers to metadata-eligible records; usable sensor counts
and complete forest-training counts can be lower. If `history` is malformed,
received count is zero after sanitization and `errors.history` explains why.

Score normalization is `clip(-score_samples, 0, 1)` for the forest, with strict
anomaly cutoff `model.isolation_forest.score_threshold`, or `d/(d+3)` for baseline,
where d is the largest available deviation (strict cutoff 0.5). Baseline reports
an anomaly if any evaluable sensor is unusual, normal only when all are evaluable
and normal, otherwise insufficient data. The scales are not calibrated against
each other. `score_normalization` contains the implemented formula string.

Forest fallback reasons are `invalid_current_metadata`, `incomplete_current_sensors`,
`insufficient_complete_history`, `constant_history`; null means it was used.
Invalid current metadata prevents training/comparison and leaves trends unknown.
Quality is invalid for invalid current metadata, partial for sensor/history errors,
otherwise valid. A valid payload may still have insufficient history. A partial
payload can still show an anomaly on an evaluable sensor; quality must remain visible.

Trends fit least squares over elapsed historical time. The direction is stable
when absolute fitted change across the observed span is at most the same floor
(5 beats/min, 1 SpO2 percentage point, 0.5 degC); otherwise the slope sign selects
increasing/decreasing. Unknown trends have null slope/change. Trend timestamps
are ISO strings with offsets; current response timestamps preserve the input string.

## 6. Expected behavior and HTTP boundary

| Input | Expected ML result |
| --- | --- |
| `examples/normal.json` | normal, quality valid, baseline fallback |
| `examples/anomaly.json` | anomaly, quality valid, baseline fallback |
| `examples/isolation_normal.json` | normal, quality valid, Isolation Forest |
| `examples/isolation_anomaly.json` | anomaly, quality valid, Isolation Forest |
| Current valid record without history | insufficient_data, null flag/score, quality valid |
| `examples/invalid.json` | insufficient_data, quality partial, invalid measurements null |
| Direct function call with `{}`, `None`, `[]` or a string | structured insufficient_data result, quality invalid |

The example route returns HTTP 200 for JSON objects reaching ML, including quality
errors. FastAPI request validation can return HTTP 422 for invalid JSON, missing
bodies or non-object bodies before ML runs. These HTTP validation responses use
FastAPI's error shape, not the ML output schema. Backend owners can establish a
different HTTP error policy explicitly; do not silently turn insufficient data into
normal or catch unexpected runtime/model failures and invent a successful ML result.
The example is intentionally not a database ingestion service.

## 7. Verify the contract without starting a backend

```powershell
py -m pytest ml-engine/tests -v
py -m pytest ml-engine/tests/test_integration_contract.py -v
```

Contract tests import the real public function, assert its signature, encode with
strict JSON (`allow_nan=False`), and validate full outputs against the schema for
both detectors, partial/invalid inputs and missing history. They check ID-specific
history behavior and ensure the schema detects missing fields/wrong units.
The optional FastAPI test imports the example, checks its route registration and
directly calls its handler; it never starts a server. Install integration requirements
to run that test (otherwise just that example test is skipped). No clinical/model
accuracy results or end-to-end backend verification are implied.

Verified run: `py -m pytest ml-engine/tests -v` returned **77 passed in 3.54s**
on Python 3.14.7 / pytest 9.2.0, with FastAPI 0.162.7, scikit-learn 1.9.1 and
jsonschema 4.26.0 installed. All 61 prior tests remain unchanged; all 16 new
contract/example cases ran, with no skips. No HTTP server was started.
