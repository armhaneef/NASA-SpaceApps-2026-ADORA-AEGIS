# Phase 4: ML integration and saved analyses

Backend-local API draft, based on Member 2's `ml-engine/INTEGRATION.md` and
`aegis_ml.analyze_health(payload: dict) -> dict`. No ML algorithms are implemented
in the backend. No other module or shared contract was changed.

## API

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/health/{astronaut_id}/analyses` | Execute requested mode, save result, return 201 |
| GET | `/health/{astronaut_id}/analyses` | List saved analyses, newest generation first |
| GET | `/health/{astronaut_id}/analyses/latest` | Latest saved analysis; 404 if none |
| GET | `/health/{astronaut_id}/analyses/{analysis_id}` | Retrieve one result scoped to astronaut |

GET requests do not run ML or write records. List accepts `limit` (1–1000,
default 100) and `offset` (nonnegative, default 0). An empty list returns `[]`.
Latest is ordered by backend generation time, then database ID, and may be a
mock; always inspect `is_mock`. A missing astronaut or inaccessible analysis
returns 404. Invalid requests return 422. No suitable input, unsupported
provenance, or deletion of an astronaut with stored analyses returns 409.

Example POST body:

```json
{
  "mode": "mock",
  "source": "synthetic_example",
  "history_limit": 100
}
```

`source` is required. `mode` defaults to `mock`; allowed values are `mock` and
`local`. `history_limit` is 0–200 earlier unique instants, not a count of individual
measurements. Optional `timestamp` chooses an exact current measurement instant
and requires a timezone. Without it, use the most recent supported measurement
instant for this astronaut and source. An unknown exact instant returns 409.

Mock success is explicitly `status: "mock"`, `is_mock: true`,
`model_version: "backend-mock-1.0"`, `ml_result: null`, and null anomaly flag and
score. It performs no analysis, does not claim normal health, and needs no ML
dependency or network connection. The mock still requires stored numeric input
so its provenance and persistence can be tested meaningfully.

`local` lazily imports Member 2's public function. Import/dependency failures or
execution failures return 503 with a safe message. Invalid engine responses
return 502. No analysis is stored on these failures. There is no silent mock
fallback: the caller must explicitly request mock mode.

## Input preparation policy

`heart_rate`, `spo2`, and `skin_temperature` feed this ML handoff. The legacy
`temperature` field is eligible only when the request explicitly includes
`temperature_is_skin: true`. Explicit `skin_temperature` wins at the same instant
if both temperature fields exist, regardless of insertion order. Without that
confirmation, legacy temperature rows do not select the current/history instants.
Readings are selected for the exact astronaut and requested source; source must
start with `synthetic`, and all selected readings must have `is_simulated=true`.
Other provenance is rejected, never relabelled. A source declaration alone is
not proof that a reading was simulated.

Current measurements must have exactly the same timestamp. There is no forward
fill or blending of asynchronous readings. History is the most recent bounded
set of strictly earlier unique instants, sent oldest first. The current instant
and later data never enter history. Per instant and type, the greatest database
ID wins for duplicate readings. These are input-selection rules, not baseline
or anomaly logic. The window is a draft demo policy, not curated clinical data.

Stored rows are preserved unchanged. During input preparation, `bpm` is normalized
to equivalent `beats/min`, and `skin_temperature` maps to ML's `temperature`.
Both mappings apply to current data and history and are recorded in
`preparation_notes`. Other units, missing sensors, and source values are passed
unchanged. Member 2's engine reports missing/wrong-unit/out-of-domain sensors
via its quality fields. Values are not clipped or imputed. A
real result with insufficient history remains `insufficient_data`, with null
flag/score, never normal. The backend does not reproduce the ML thresholds.

## Storage and interpretation

Startup adds `health_analyses` to SQLite without changing existing tables.
Each row has an ID, astronaut foreign key, timezone-aware generation timestamp,
and a complete JSON result snapshot. It restricts astronaut deletion even if
sensor rows have subsequently been removed through maintenance. There are no
analysis update/delete endpoints in this phase.

The response includes:

- `analysis_timestamp`: backend generation time; `measurement_timestamp`: current
  input time. These represent different events.
- `is_mock`, `status`, nullable `anomaly_detected` and `anomaly_score`, model
  version, original `data_source`, and explanatory context.
- `prepared_input`: exact JSON payload sent to the ML engine, with its history.
- `input_readings`: chosen input-row snapshots including database IDs, original
  units, source, sensor type, quality, timestamps, and simulation flags.
- `ml_result`: entire validated Member 2 response including nulls and additive
  fields, quality warnings, baselines, trends, model selection, and scoring details.
- `preparation_notes`: explicit unit/field mappings and temperature precedence
  decisions, with original row IDs. Older saved results default to an empty list.

`affected_measurements` lists the engine's **baseline sensor anomaly flags**;
it is not an attribution of an Isolation Forest joint result and can disagree
with that overall result. Scores from different methods are not calibrated
against one another and are not medical probabilities. No alerts, clinical
thresholds, independent baseline calculations, or health advice are generated.

Output validation uses `jsonschema` and a backend-owned snapshot of Member 2's
schema at `contracts/ml-analysis-output.schema.json`. It validates every current
required field, permits additive fields, rejects non-JSON/nonfinite values,
and checks identity, status/flag/score and detector consistency. The schema is a
copy, not an independent redesign. Its SHA256 at adoption is
`8BE0587E573CFB3D133683A9FD49B1399B6EC8CE71516E216B2B582A621B1D17`.
Future ML schema versions require a reviewed backend update. The backend starts
without the sibling module because loading ML and its dependencies is lazy.

## Verify in PyCharm and Swagger

Use `backend/.venv/Scripts/python.exe` as the interpreter and `backend` as the
working directory. From the PyCharm terminal at the repository root:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Restart an already running server after installing the new dependency. Open
http://127.0.0.1:8000/docs. Use the Phase 3 walkthrough to create a fictional
astronaut and ingest a `heart_rate` reading with `source: "synthetic_example"`,
`unit: "beats/min"`, and `is_simulated: true`.

1. Execute **POST /health/{astronaut_id}/analyses** using that ID and the mock
   body above. Expect 201, a database ID, and the explicit mock fields.
2. Execute the list, `/latest`, and `/{analysis_id}` GET routes. Expect exactly
   the saved snapshot. Repeating GET does not create a new record.
3. Request `mode: "local"` without local ML configured. Expect 503 and no new
   record, while astronaut/sensor APIs and explicit mock requests still work.

To enable the optional real local engine, from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
$env:PYTHONPATH = (Resolve-Path ..\ml-engine).Path
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a PyCharm Run Configuration, add `PYTHONPATH=<absolute repository path>\ml-engine`
to environment variables. This configures imports without changing shared files.
The optional installation includes scikit-learn and NumPy/SciPy in the backend's
own environment only. First installation needs package downloads; subsequent
local analysis needs no network or cloud service.

Repeat POST with `mode: "local"`. With only one sensor and no history, expect a
real `insufficient_data` result, `is_mock: false`, null flag/score, and full ML
quality details. Additional complete historical instants allow Member 2's engine
to choose its detector. Successful POSTs create separate snapshots, including
repeated identical requests; there is no caching/idempotency policy yet.

Backend tests use temporary databases and stubs for error paths. Optional
real-engine tests read the sibling module/fixtures and skip if it or scikit-learn
is absent. Tests never edit the ML module or the demo database.

Verified in the backend Python 3.12 environment: **79 passed**, no skips, with
one existing TestClient deprecation warning. Real-engine checks cover the HTTP
adapter's insufficient-data path and the ML module's normal/anomaly fixtures for
both baseline and Isolation Forest methods. These are software integration
checks, not an evaluation of medical accuracy or model performance.

The Phase 6 follow-up is documented in [PHASE6_ML_INTEGRATION.md](PHASE6_ML_INTEGRATION.md).
Member 2 should confirm the source/unit mappings, synchronized-input selection,
history window, schema version, and meaning of summary fields. Members 5 and 6
should review the response envelope before integration. These routes do not yet
implement the Digital Twin endpoint or baseline/alert APIs.
