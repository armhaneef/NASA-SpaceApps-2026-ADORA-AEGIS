# Phase 6 ML integration follow-up

This backend-only change addresses the ML static review. It does not implement
Twin APIs, alerts, frontend CORS or Member 3's assistant. No ML model, shared
fixture or other member's source was changed.

## Input preparation

- Heart-rate `bpm` maps to identical numeric `beats/min` for ML, including history.
- `skin_temperature` maps to ML's `temperature` in `degC`.
- Legacy `temperature` is not assumed to be skin temperature. A caller may set
  `temperature_is_skin: true` only after confirming the source measures skin.
  When false (default), legacy temperature is excluded from input selection.
- If both temperature fields occur at one instant, explicit `skin_temperature`
  takes precedence, independently of insertion order. An invalid explicit skin
  reading does not fall back to a more plausible legacy value.
- Existing same-astronaut, same-source, exact-instant grouping and strictly earlier
  history selection remain. Duplicate original measurement types use the latest ID.
- Original database rows are untouched. Responses retain original `input_readings`,
  normalized `prepared_input`, and a new `preparation_notes` list for traceability.
  With the legacy opt-in, snapshots also retain legacy candidates superseded by
  explicit skin readings. Old saved analyses default to empty preparation notes.

Member 2 owns input-domain validation: heart rate 20–250, skin temperature 10–50,
SpO2 0–100, inclusive. The backend's storage domain is intentionally broader for
some measurements. It passes those readings unchanged to ML, without clipping,
dropping rows or inventing values. ML sanitizes invalid measurements to null and
returns explicit per-field quality errors. The backend stores and returns that
full response. Insufficient data stays unknown, not normal. The real engine may
still flag another evaluable sensor despite partial quality; its verdict is never
replaced by backend logic. These bounds are prototype input domains, not clinical
alert thresholds. Physically invalid ingestion values already rejected by Phase 3
(e.g. negative heart rate or SpO2 above 100) still return 422 before ML.

## Run and verify in PyCharm

Use the existing `backend/.venv/Scripts/python.exe` interpreter. From `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -r requirements-ml.txt
$env:PYTHONPATH = (Resolve-Path ..\ml-engine).Path
.\.venv\Scripts\python.exe -B -m pytest tests/test_ml_end_to_end.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

For a PyCharm Run Configuration, use module `uvicorn`, parameters
`app.main:app --reload --host 127.0.0.1 --port 8000`, working directory `backend`,
and environment variable `PYTHONPATH=<absolute repository path>\ml-engine`.
The runtime must import `aegis_ml` and scikit-learn from the backend interpreter.
This is explicit process configuration; the backend does not modify global
Python settings or automatically switch mock requests into real inference.

At `/docs`, create a fictional astronaut and ingest numeric records with the
same timestamp, source `synthetic_example`, `is_simulated: true`, and these fields:

| measurement_type | value | unit |
| --- | --- | --- |
| heart_rate | 72 | bpm |
| spo2 | 98 | % |
| skin_temperature | 33 | degC |

Execute `POST /health/{astronaut_id}/analyses`:

```json
{
  "mode": "local",
  "source": "synthetic_example",
  "history_limit": 100,
  "temperature_is_skin": false
}
```

Expect 201, `is_mock: false`, normalized input and preparation notes. Without
history, expect `insufficient_data`, null verdict/score, and valid input quality.
Retrieve the ID through the analysis GET endpoint to confirm persistence. If
using legacy `temperature` instead, confirm skin semantics and explicitly set
`temperature_is_skin: true`. Do not set it for cabin or core temperature.

Adding separate earlier complete instants enables Member 2's baseline detector;
at least 32 complete historical records with variation are required for its
Isolation Forest path. Do not manually synthesize clinical thresholds to force
a verdict. The tests use Member 2's deterministic example data for known outcomes.

## End-to-end tests

`tests/test_ml_end_to_end.py` starts an actual Uvicorn subprocess on an ephemeral
localhost port, with the documented ML import path and real dependencies. It uses
the real FastAPI app and local ML adapter, not a fake ML callable. Only the database
dependency is redirected to a temporary SQLite file. It stops the subprocess when
finished; the demo database is not changed.

All scenario data passes through astronaut creation and sensor ingestion APIs,
then the analysis POST explicitly requests `mode: "local"`. List, latest and
individual analysis GETs verify saved output. A second astronaut's history is
excluded and cannot retrieve the first astronaut's saved analysis.

The 11 cases cover baseline normal/anomaly, insufficient history, Isolation Forest
normal/anomaly with 64 eligible historical records, temperature precedence in
both insertion orders, explicit legacy opt-in, both sides of the ML input ranges,
and inclusive range boundaries. Assertions check method selection, history counts,
quality errors, normalized payloads and preservation of stored readings.

The tests skip explicitly if optional scikit-learn or the sibling ML module is
absent. A passing mock-only suite must not be reported as real runtime validation.
Missing dependencies/imports in an otherwise configured runtime fail server startup
in these tests. The runtime process has no provider override or ML mock installed.

Verified locally: **11 real-HTTP ML cases passed**, including both forest fixtures.
These validate integration behavior, not medical accuracy or clinical suitability.
