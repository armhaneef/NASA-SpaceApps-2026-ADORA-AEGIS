# React integration handoff

Current implemented backend behavior, prepared for Member 5. These notes do not
amend shared contracts outside `backend/`. Final UI field requirements and any
shared contract changes still require team agreement.

## Run locally

Use `backend/.venv/Scripts/python.exe` in PyCharm, with working directory `backend`.
From the repository root:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:AEGIS_CORS_ORIGINS = '["http://localhost:5173"]'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

React should use API base URL `http://127.0.0.1:8000` and run from the approved
browser origin `http://localhost:5173`. A page opened at `http://127.0.0.1:5173`
has a different origin and is not permitted by default. The API hostname and
browser page origin do not have to match.

`AEGIS_CORS_ORIGINS` is a JSON array of explicit HTTP/HTTPS origins. Unset means
`["http://localhost:5173"]`; `[]` disables cross-origin access. A supplied list
replaces the default. Only add additional origins after team approval. Paths,
queries, fragments, credentials, wildcard patterns and literal `null` origins
are rejected at startup. Root trailing slashes are normalized away.

Settings are read when the app is imported. Restart after environment changes.
In a PyCharm Run Configuration, set `AEGIS_CORS_ORIGINS` in environment variables.
`.env.example` is a template, not automatically loaded configuration. If using a
local `.env` copy, start Uvicorn with `--env-file .env` (supported by the existing
Uvicorn standard dependencies). No new dependency was introduced for settings.

Allowed methods are GET, POST, PATCH and DELETE; preflight OPTIONS is handled by
the CORS middleware. JSON Content-Type is permitted. Credentials/cookies are not
enabled. There is no authentication layer yet; CORS is browser access policy, not
authorization or protection from non-browser requests. Backend remains bound to
localhost for this development setup.

## Browser request example

This is reference code for Member 5, not a change to the frontend:

```javascript
const API = 'http://127.0.0.1:8000';

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API}${path}`, options);
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map(error => error.msg).join('; ')
      : body.detail;
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return body;
}

const astronauts = await apiRequest('/astronauts');
const created = await apiRequest('/astronauts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    astronaut_id: 'AST-UI-001', name: 'Mira Sen (fictional)',
    mission_id: 'MARS-SIM-01', mission_role: 'Engineer'
  })
});
```

Do not call `response.json()` for a successful DELETE (204). Do not use Fetch's
`no-cors` mode: it produces an unreadable opaque response. Network failures and
denied origins can appear as Fetch errors before a JSON error is available.

## Example JSON responses

IDs and timestamps below are illustrative; generated values vary. Full schemas,
including complete analysis payloads, are available at `/openapi.json` and `/docs`.
The examples preserve existing response shapes; there is no new shared envelope.

### Profile: POST 201, GET/PATCH 200

```json
{
  "astronaut_id": "AST-UI-001",
  "name": "Mira Sen (fictional)",
  "mission_id": "MARS-SIM-01",
  "mission_role": "Engineer",
  "profile_metadata": {"fictional": true},
  "created_at": "2026-11-14T10:00:00Z"
}
```

List returns an array of profiles. PATCH accepts only changed fields, for example
`{"mission_role":"Commander"}`. Metadata updates replace the whole object.
Astronaut IDs and creation timestamps are immutable. Deletion returns 409 when
readings or analyses reference the profile.

### Reading arrays: ingest 201, latest/history 200

POST `/health/ingest` with the row below, omitting `id`, to create a reading.
The same array shape is returned by latest/history:

```json
[
  {
    "astronaut_id": "AST-UI-001",
    "timestamp": "2026-11-14T10:00:00Z",
    "sensor_type": "smart_band",
    "is_simulated": true,
    "quality": "simulated",
    "measurement_type": "heart_rate",
    "value": 78,
    "unit": "bpm",
    "source": "synthetic_example",
    "id": 1
  }
]
```

Use `skin_temperature` in `degC` for skin data. The complete accepted registry
and grouped-input format are in [PHASE3_API.md](PHASE3_API.md). The shared fixture
still needs explicit sensor type and simulation metadata before ingestion.

Latest means newest by measurement timestamp **per measurement type**, ordered by
type; ID breaks timestamp ties. This can combine indicators from different instants
and sources, so inspect each row's timestamp and provenance. It does not mean the
indicators are synchronous or sufficiently recent for a particular display.

History is oldest first, with inclusive `start`/`end` bounds and ID tie-breaking.
Both endpoints accept `measurement_type`. History accepts `limit` (default 100,
maximum 1000) and nonnegative `offset`. Use `URLSearchParams` for date filters,
especially offsets containing `+`. Empty data for an existing astronaut is `[]`;
unknown astronauts return 404. Units are preserved in retrieval, so charts must
not combine incompatible units or measurement types automatically.

### Saved mock analysis: POST 201, GET 200

POST `/health/AST-UI-001/analyses` with
`{"mode":"mock","source":"synthetic_example"}` after ingesting the reading above:

```json
{
  "astronaut_id": "AST-UI-001",
  "analysis_timestamp": "2026-11-14T10:01:00Z",
  "measurement_timestamp": "2026-11-14T10:00:00Z",
  "status": "mock",
  "is_mock": true,
  "anomaly_detected": null,
  "anomaly_score": null,
  "affected_measurements": [],
  "explanations": ["MOCK: development placeholder only. No ML model was invoked; no health assessment, anomaly verdict, or score is available."],
  "model_version": "backend-mock-1.0",
  "data_source": "synthetic_example",
  "prepared_input": {
    "astronaut_id": "AST-UI-001",
    "timestamp": "2026-11-14T10:00:00+00:00",
    "data_source": "synthetic_example",
    "heart_rate": {"value": 78, "unit": "beats/min"},
    "history": []
  },
  "input_readings": [
    {
      "astronaut_id": "AST-UI-001",
      "timestamp": "2026-11-14T10:00:00Z",
      "sensor_type": "smart_band",
      "is_simulated": true,
      "quality": "simulated",
      "measurement_type": "heart_rate",
      "value": 78,
      "unit": "bpm",
      "source": "synthetic_example",
      "id": 1
    }
  ],
  "ml_result": null,
  "preparation_notes": [
    "Legacy temperature is excluded unless temperature_is_skin=true; only explicitly labelled skin_temperature is mapped to ML temperature.",
    "Reading 1: bpm normalized to beats/min for ML only."
  ],
  "id": 1
}
```

Use `mode: "local"` explicitly for real ML; it requires the local module and its
dependencies. See [PHASE6_ML_INTEGRATION.md](PHASE6_ML_INTEGRATION.md) for setup
and temperature semantics. Null anomaly flag/score means unknown, not normal or
zero. Real statuses are `normal`, `anomaly`, and `insufficient_data`; mock remains
distinct. `ml_result` preserves full quality, baseline, method and trend metadata.
Baseline sensor flags are not attributions of an Isolation Forest joint result.
Scores are not medical probabilities.

Analysis GET `/latest` means latest generation time, including mocks. It does
not run analysis. GET list is newest first, default limit 100/max 1000, and includes
full snapshots. Prefer `/latest` for a current display rather than repeatedly
fetching the entire history. Repeating an analysis POST saves a new result; it is
not idempotent. No background analysis, streaming or automatic alerts exist.

### Assistant mock: 200

POST `/ai/assistant` with
`{"astronaut_id":"AST-UI-001","question":"Explain this prototype","mode":"mock"}`:

```json
{
  "astronaut_id": "AST-UI-001",
  "answer": "MOCK: The assistant is not connected. This is a development placeholder; no question interpretation or health assessment was performed.",
  "assistant_version": "backend-assistant-mock-1.0",
  "is_mock": true,
  "limitations": ["No AI model or knowledge retrieval was invoked.", "This placeholder provides no medical advice."],
  "response_timestamp": "2026-11-14T10:02:00Z",
  "mode": "mock",
  "status": "mock",
  "data_source": "backend_mock",
  "context": {"analysis": null}
}
```

Explicit optional `analysis_id` selects context for this astronaut only. Without
it, no analysis is automatically forwarded. Local AI is unconfigured and returns
503; real assistant implementation remains Member 3's work.

### Errors

Missing astronaut (404):

```json
{"detail": "Astronaut not found"}
```

Invalid request example (422):

```json
{"detail": [{"type": "missing", "loc": ["body", "name"], "msg": "Field required"}]}
```

`detail` can be a string or validation-error array. Union ingestion validation can
report multiple branch errors; use locations/messages rather than depending on
an exact error count. Other expected statuses include 409 (duplicate ID, protected
deletion or no eligible ML input), 502 (invalid provider output), 503 (unavailable
provider), and 504 (assistant-reported timeout). See the individual phase documents
for each operation. JSON content errors should be distinguished from CORS/network
failures; preflight responses themselves are middleware text, not the API envelope.

## Verify browser access

Open `/docs` for endpoint verification. Swagger on the backend origin does not
test cross-origin browser access. In the React page's browser console at
`http://localhost:5173`, run the Fetch examples above or:

```javascript
fetch('http://127.0.0.1:8000/health')
  .then(response => response.json()).then(console.log);
```

Expect `{"status":"ok"}`. POST with JSON triggers a browser preflight; the network
panel should show a successful OPTIONS with the exact allow-origin value.
Automated checks, from `backend`:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/test_cors.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
```

## Decisions for Member 5

- Confirm needed dashboard fields, metadata keys, chart metrics and unit policy.
- Confirm how the UI distinguishes missing, stale, mock and insufficient data.
  No freshness cutoff has been agreed; inspect timestamps rather than inventing one.
- Confirm polling cadence, expected volume, and pagination behavior; there are
  no WebSocket/SSE endpoints, automatic retries or frontend caching implemented here.
- Confirm who triggers analysis POSTs and explicitly selects real versus mock mode.
- Confirm the browser origin, API base URL and any additional approved origins.
- Confirm whether the UI needs an aggregated dashboard response; none is implemented.
- Coordinate alerts and the proposed Twin response with Member 6. Their endpoints
  are not available and must not be assumed from proposed names.
