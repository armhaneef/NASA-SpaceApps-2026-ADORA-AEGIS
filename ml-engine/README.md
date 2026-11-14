# AEGIS ML engine — Phase 2

Working personalized baseline detector for **synthetic data only**. This is not
a clinically validated system and must not support medical or mission decisions.
Includes Isolation Forest, personalized baseline fallback and descriptive historical
trends. Forecasts, persistence and HTTP endpoints are not implemented.

## Run and integrate

Member 4: see [INTEGRATION.md](INTEGRATION.md) for copy-paste backend instructions,
the standalone FastAPI example and complete machine-readable output schema.

From the repository root with Python 3.11+ (tested on Python 3.14.7):

```powershell
py -m pip install -r ml-engine/requirements.txt
py -m pytest ml-engine/tests -v
$env:PYTHONPATH = (Resolve-Path ml-engine).Path
py -c "import json; from aegis_ml import analyze_health; print(json.dumps(analyze_health(json.load(open('ml-engine/examples/normal.json'))), indent=2, allow_nan=False))"
```

Backend callers add `ml-engine/` to the Python import path and use
`from aegis_ml import analyze_health`, then call `analyze_health(payload)`.
Runtime requires scikit-learn and its NumPy/SciPy dependencies; pytest is the test dependency.
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
such as `co2` and `respiration_rate` are ignored. Missing values, booleans,
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
This fallback is a deterministic deviation heuristic, not a trained predictive model.
Supply curated baseline history: historical anomalies can distort the baseline.
There is no recency window, activity adjustment or contamination removal.

## Isolation Forest and selection

The joint model uses features in fixed order: `heart_rate`, `spo2`, `temperature`.
It trains only when there are at least **32 complete eligible historical records**,
at least two distinct historical feature vectors, valid current metadata, and all
three current sensors are valid. The count and variation checks are prototype
engineering choices, not evidence of sufficient statistical or clinical validity.
Partial historical rows remain usable by per-sensor baselines and trends but are
excluded from joint training. There is no imputation or cross-astronaut pooling.

Each call fits 100 trees, `max_samples="auto"` (up to 256 samples per tree),
`contamination=0.05`, `random_state=42`, `n_jobs=1`, using time-sorted history.
The current record is scored only after fitting and never enters training.
An anomaly has `score_samples(current) < offset_`. The contamination parameter
sets a training-score cutoff; it is not a medical prevalence estimate.
See the [official scikit-learn API](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html).

Otherwise the Phase 1 baseline logic determines the result, with an explicit
`model.isolation_forest.fallback_reason`: `invalid_current_metadata`,
`incomplete_current_sensors`, `insufficient_complete_history`, or `constant_history`.
The first applicable reason wins. The model metadata includes the eligible training
record count even when fitting is skipped; `used` indicates whether fitting/scoring
actually occurred. Required-library installation failures are not silently hidden.

Identical inputs give identical results within the same dependency environment.
Unique-timestamp history can be reordered without changing results. Duplicate instants
retain the original first-eligible-wins policy. The response records the scikit-learn
version; bit-for-bit results across library versions/platforms are not guaranteed.
Training is in-memory on every call; there is no saved model or evaluation claim.

## Normalized anomaly score

`anomaly.normalized_score` is between 0 and 1 when evaluable, with larger values
indicating greater unusualness. It is **not a medical probability**, calibrated risk,
or a prediction of a future condition.

- Isolation Forest: `clip(-score_samples(current), 0, 1)`. scikit-learn negates
  the original isolation anomaly score, so negation restores its direction; clipping
  guards numerical bounds. `model.isolation_forest.score_threshold = -offset_`
  exposes the fitted cutoff. Scores strictly above this cutoff are anomalous.
- Baseline fallback: `d / (d + 3)`, where `d` is the largest available per-sensor
  deviation score. A score strictly above 0.5 is anomalous. If no sensor is anomalous
  and some cannot be evaluated, overall status remains `insufficient_data` and the
  score is null. A detected anomaly on partial data still returns its score.

These method-specific scales are not calibrated against one another. Always inspect
`anomaly.method`, data quality and model metadata when explaining scores.

## Descriptive historical trends

`trends` has one entry per sensor, based only on its eligible historical readings,
sorted by actual timestamp. The current reading is excluded. At least three valid
unique instants are required; otherwise direction is `unknown` and slope/change
are null. Each eligible sensor is analyzed independently of joint-model readiness.

Ordinary least squares fits values against elapsed time, accounting for irregular
sampling. `slope_per_hour` reports sensor units per hour; `fitted_change` is slope
times the full observed span. The direction is `stable` when the absolute fitted
change is at most 5 beats/min, 1 percentage point SpO2, or 0.5 degC respectively.
Otherwise it is `increasing` or `decreasing` according to the slope sign.
These illustrative tolerances reuse the baseline scale floors. The output includes
sample count, change threshold and start/end timestamps. Trends describe observed
history without forecasting; they have no clinical interpretation or confidence claim.

## Output contract (schema_version 1.0, additive Phase 2 fields)

- `astronaut_id`, `timestamp`, `data_source`: input metadata; non-string values become null.
- `sensor_readings`: sanitized, unit-bearing values.
- `baseline`: per-sensor `count`, `mean`, `std`, effective `scale`, `unit`, `ready`.
- `anomaly`: overall `status`, nullable `is_anomaly`, per-sensor status and deviation
  scores; adds `method`, `normalized_score`, and `sensor_method`.
- `trends`: per-sensor historical direction, slope, fitted change, count and window.
- `data_quality`: status, current-field errors, indexed history issues and received/accepted record counts.
- `model`: active method name, engine version `2.0.0`, existing minimum history,
  deviation threshold and prototype labels; adds `isolation_forest` metadata and
  `score_normalization`. The deviation threshold still describes the baseline only.

With baseline fallback, overall status is `anomaly` if any evaluable sensor is unusual, `normal` only
when all three are evaluable and normal, otherwise `insufficient_data`.
`is_anomaly` is null for insufficient data. Invalid current identity, timestamp
or provenance prevents comparison. Quality is `invalid` for invalid current
metadata, `partial` for sensor/history errors, otherwise `valid`. Valid input can
still have insufficient history. When Isolation Forest is used, its joint result
determines overall status and score. `anomaly.sensors` always remains the baseline
explanation (`sensor_method` identifies it); it is not an attribution of the forest
result and may disagree with the joint result. Existing field names, units, nullable
booleans and status strings are preserved. Consumers should allow additive fields
and use `anomaly.method` or `model.name` to explain which detector was selected.
Accepted history counts refer to metadata-eligible
records; per-sensor counts report usable values. Output supports strict JSON.

## Examples and layout

`examples/normal.json`, `examples/anomaly.json` and `examples/invalid.json` are
fixed synthetic fixtures with expected statuses `normal`, `anomaly` and
`insufficient_data` respectively. The invalid example has partial data quality.
These original fixtures continue to exercise the baseline fallback.

`examples/isolation_normal.json` and `examples/isolation_anomaly.json` contain 64
complete fabricated historical records and exercise the joint detector.
`examples/trends.json` demonstrates increasing heart rate, decreasing SpO2 and
stable skin temperature. Regenerate these three Phase 2 fixtures deterministically:

```powershell
py ml-engine/examples/generate_phase2.py
```

`aegis_ml/validation.py` validates inputs, `baseline.py` calculates baselines and
scores, `isolation.py` implements the joint forest, `trends.py` calculates historical
trends, and `pipeline.py` exposes `analyze_health`. The existing `models/`,
`preprocessing/` and `evaluation/` folders remain available for later experiments.
Tests cover examples, personalization, malformed inputs, history filtering,
constant history, threshold boundaries, partial data, forest selection and scoring,
time-based trends, output compatibility and repeatability.

## Verification

Actual run: `py -m pytest ml-engine/tests -v` on Python 3.14.7 / pytest 9.2.0:
**61 passed in 3.09s**, including all 34 unchanged Phase 1 tests. These are
synthetic software behavior checks, not model accuracy, clinical evaluation or
evidence of validated health prediction. Backend/assistant services were not changed
or exercised end-to-end; compatibility is checked at the Python/JSON contract boundary.
