# Backend

The backend owns the HTTP API boundary. Its initial FastAPI application exposes
a health check so the service can be started and checked before other modules
are integrated.

**Inputs:** HTTP requests and validated numeric sensor records. Shared conventions
are in [`docs/data-schema.md`](../docs/data-schema.md); the implemented backend
formats and required provenance extensions are in [PHASE3_API.md](PHASE3_API.md).

**Outputs:** JSON responses described below and in
[FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md). The shared
[`docs/api-contracts.md`](../docs/api-contracts.md) still documents only the initial
health endpoint and has not been edited by backend development.

## Phase 1 setup in PyCharm

Python 3.12 is available locally and is compatible with this backend. Keep the
backend environment separate from other modules. From the repository root:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Using the executable directly avoids PowerShell activation-policy problems.
For runtime-only installation, use `requirements.txt` instead. First installation
requires package downloads; the installed health API runs without internet.

In PyCharm, select `backend/.venv/Scripts/python.exe` as the interpreter. Create
a Python run configuration with module name `uvicorn`, parameters
`app.main:app --reload --host 127.0.0.1 --port 8000`, and working directory
`backend` (the absolute backend path in your checkout). Stop with Ctrl+C in the
terminal or the IDE Stop button.

## Verify

Open http://127.0.0.1:8000/health: expect HTTP 200 and `{"status":"ok"}`.
Open http://127.0.0.1:8000/docs, expand **GET /health**, select **Try it out**,
then **Execute**. Expect the same response. `/openapi.json` provides the schema
for other developers. Swagger UI loads assets from a CDN, so its interactive
page may require internet even though the API and OpenAPI JSON work offline.

From `backend`, run automated checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

`app/main.py` assembles the application; `app/routes/health.py` handles the HTTP
endpoint and declares its response shape. We retain the existing `routes/`
directory rather than introducing a duplicate `api/` directory. Development
dependencies are separate from runtime dependencies.

## Scope and next phase

Phase 3 adds astronaut CRUD, validated ingestion, latest readings, and history
on top of Phase 2 storage. Phase 4 adds a labelled mock/local ML adapter and saved
analyses. Phase 5 adds an assistant boundary with labelled mock replies and a
replaceable provider adapter. Real AI content and clinical functionality are not
implemented. No other module is required to start this server or use mock mode.

The shared health contract is preserved. Before ingestion implementation, resolve
the difference between `docs/data-schema.md` (grouped readings, e.g. `beats/min`)
and the proposed per-measurement format (`bpm`, source and simulation metadata)
with the team lead. The root README's member assignments also differ from the
current backend assignment. These shared files have not been changed.

## Phase 2: local storage

Install the updated dependencies and start the app from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Startup creates missing tables in `backend/aegis.sqlite3`. The path is based on
the source file, so changing the terminal working directory cannot put the
database in another module. SQLite is included with Python; no database server
or internet connection is needed after installation. The database file is
ignored by the repository's existing Git rules.

- `app/database/connection.py`: engine (database connection configuration),
  initialization, and a session dependency for future routes. A session groups
  database operations; `commit()` saves them, and closing an uncommitted session
  rolls back its changes. SQLite foreign-key enforcement is enabled explicitly.
- `app/models/models.py`: `Astronaut` and `SensorReading` table definitions.
  Each reading references an existing astronaut. Deleting an astronaut with
  readings is restricted to preserve history. IDs are unique primary keys.
- `app/main.py`: initializes tables during FastAPI startup, without inserting
  sample records or replacing existing data.
- `tests/conftest.py` and `tests/test_database.py`: temporary databases for
  persistence, relationships, UTC timestamps, duplicate IDs, and unknown IDs.

Astronauts store ID, name, mission ID, role, JSON profile metadata, and creation
time. Replace the metadata dictionary when updating it so SQLAlchemy detects the
change. Sensor readings store a numeric value, measurement and sensor types,
unit, source, explicit `is_simulated` flag, optional quality label, and timestamp.
Timezone-aware timestamps are normalized to UTC and returned with UTC timezone
information. Naive timestamps are rejected. No clinical thresholds or unit
conversions are assumed. Waveforms are outside this numeric MVP model.

### Verify in PyCharm

Use the existing backend interpreter and working directory from Phase 1. Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Phase 2 introduced eight checks. All tests use temporary SQLite files, including app startup
in the health tests; they do not modify `aegis.sqlite3`.

To inspect persistence manually, open PyCharm's Python Console with `backend` as
its working directory and `backend/.venv` as its interpreter, then execute:

```python
from sqlalchemy.orm import Session
from app.database.connection import engine, init_db
from app.models.models import Astronaut

init_db()
with Session(engine) as session:
    if session.get(Astronaut, "AST-DEMO-001") is None:
        session.add(Astronaut(
            astronaut_id="AST-DEMO-001", name="Mira Sen (fictional)",
            mission_id="MARS-SIM-01", mission_role="Engineer",
            profile_metadata={"fictional": True},
        ))
        session.commit()

with Session(engine) as session:
    saved = session.get(Astronaut, "AST-DEMO-001")
    print(saved.astronaut_id, saved.name, saved.mission_role)
```

Expect `AST-DEMO-001 Mira Sen (fictional) Engineer`. Close and reopen the console,
then repeat the imports and final `with` block to confirm the record persists.
This example deliberately saves a fictional record in the local demo database;
the automated tests do not. Phase 3 now exposes astronaut and sensor endpoints
in `/docs` as described below.

`create_all()` creates missing tables but does not migrate existing table
definitions. Future schema changes will need an explicit migration plan.
Standalone baseline and alert tables remain for later phases; Phase 4 stores
ML baselines within complete analysis snapshots. The internal normalized
reading model is a backend draft, not a change to the shared ingestion contract;
mapping shared records and confirming units/provenance with Member 1 comes
before ingestion. No other team member's implementation is needed for Phase 2.

## Phase 3: verify the REST APIs in PyCharm

Use `backend/.venv/Scripts/python.exe` as the interpreter and `backend` as the
working directory. No new dependencies or database schema migration is needed.
From the repository root in the PyCharm terminal:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If a previous server is running, stop it first or let its reload finish. Expect
the full test suite to pass; the existing TestClient dependency deprecation
warning may still appear. Tests exercise CRUD, validation, grouped ingestion
atomicity, missing astronauts, deletion restrictions, UTC time filters,
pagination, newest-per-type queries, and preservation of source metadata. They
override both startup initialization and request sessions to use temporary files.

Open http://127.0.0.1:8000/docs. For each request select **Try it out**, fill in
the body or path fields, then **Execute**:

1. **POST /astronauts**, using:

   ```json
   {
     "astronaut_id": "AST-API-DEMO",
     "name": "Mira Sen (fictional)",
     "mission_id": "MARS-SIM-01",
     "mission_role": "Engineer",
     "profile_metadata": {"fictional": true}
   }
   ```

   Expect 201 with the profile and `created_at`. Repeating it returns 409.
2. **GET /astronauts** and **GET /astronauts/{astronaut_id}**, using
   `AST-API-DEMO`. Expect the saved profile.
3. **PATCH /astronauts/{astronaut_id}**, using `{"mission_role":"Commander"}`.
   Expect 200 with the updated role and original name.
4. **POST /health/ingest**, using the individual JSON example in
   [PHASE3_API.md](PHASE3_API.md), changing `astronaut_id` to `AST-API-DEMO`.
   Swagger's union schema allows either a single reading or a grouped record.
   Expect 201 and an array containing a stored reading with its database `id`.
5. **GET /health/{astronaut_id}/latest** and **history**, using `AST-API-DEMO`.
   Expect that reading, including its source, unit, timestamp and simulation flag.
   Try history with `measurement_type=heart_rate`, start/end timestamps, and
   `limit`/`offset`. Omit optional fields when unused.
6. Submit the reading with `unit: "wrong"`: expect 422. Submit with an unknown
   astronaut: expect 404. **DELETE** the astronaut with stored readings: expect
   409, with the reading preserved. To verify successful deletion, create a
   different fictional profile without readings, delete it, and expect 204;
   retrieving it afterward returns 404.

These manual requests persist in your local demo database. Do not delete the
database to rerun an example; use a new fictional ID or update the existing
profile. [PHASE3_API.md](PHASE3_API.md) documents all request shapes, units,
status codes, ordering, limitations, and pending team decisions.

New schemas in `app/schemas/` validate JSON before storage. Routes in
`app/routes/astronauts.py` and `sensors.py` handle HTTP, while
`app/services/astronaut_service.py` and `sensor_service.py` perform database
operations. `app/services/errors.py` defines expected failures, translated into
HTTP responses by `app/main.py`. No shared files or other modules are modified.

## Phase 4: ML adapter and stored results

See [PHASE4_ML.md](PHASE4_ML.md) for the new analysis POST/GET endpoints, copyable
mock request, optional real-engine setup, input selection policy, output schema,
and failure behavior. Run the same backend test command above after installing
the updated requirements. A new `health_analyses` table is created on restart;
existing astronaut and sensor tables are preserved.

The adapter in `app/services/ml_adapter.py` calls Member 2's documented interface
only in explicit local mode; mock mode needs no ML dependencies. The analysis
service prepares source-preserving same-time sensor groups and earlier history,
then saves the full validated output and input snapshots. Schemas, routes, tests,
and a backend-owned copy of the ML output contract accompany the service. The
real engine remains owned by Member 2 and is not modified or duplicated here.

## Phase 5: assistant endpoint

`POST /ai/assistant` accepts an astronaut ID, question, optional selected analysis
ID, and explicit mock/local mode. Mock mode returns a static labelled placeholder
offline. Local mode returns 503 until Member 3's approved provider is wired in.
No conversations are stored and no database schema or dependency changes are
needed. Selected context preserves analysis provenance and uncertainty while
excluding profile metadata, raw readings, and sensor history.

See [PHASE5_ASSISTANT.md](PHASE5_ASSISTANT.md) for copyable `/docs` requests,
PyCharm verification, the draft provider contract, failure status codes and
remaining integration limitations. Files added are `app/schemas/assistant.py`,
`app/services/ai_adapter.py`, `app/services/assistant_service.py`,
`app/routes/assistant.py`, and `tests/test_assistant.py`. `app/main.py` registers
the route and error handlers; `app/services/errors.py` defines provider failures.
The AI module and shared files are untouched.

## Phase 6 ML review fixes

See [PHASE6_ML_INTEGRATION.md](PHASE6_ML_INTEGRATION.md) for current/history unit
normalization, explicit skin-temperature mapping and precedence, out-of-domain
ML quality handling, and real Uvicorn end-to-end tests. Raw stored readings are
preserved. Legacy `temperature` is used for ML only with the explicit analysis
request flag `temperature_is_skin: true`; `skin_temperature` needs no such flag.
Twin/alert APIs remain separate Phase 6 work. Browser integration preparation is
described below.

## Phase 6: frontend integration preparation

CORS now permits the approved React origin `http://localhost:5173` by default.
`AEGIS_CORS_ORIGINS` accepts a JSON array of explicit origins and replaces the
default; wildcard origins are rejected. Credentials are disabled. Configure this
in the PyCharm Run Configuration or terminal, and restart the backend after changes:

```powershell
$env:AEGIS_CORS_ORIGINS = '["http://localhost:5173"]'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run from `backend` using its existing interpreter. `.env.example` documents the
setting; an `.env` file is loaded only when explicitly passed with `--env-file`.
No dependency, database schema, route path or success-response shape changed.

### Implemented endpoint inventory

| Method | Path | Success |
| --- | --- | --- |
| GET | `/health` | 200, `{"status":"ok"}` |
| POST | `/astronauts` | 201, created profile |
| GET | `/astronauts` | 200, profile array; limit/offset |
| GET | `/astronauts/{astronaut_id}` | 200, profile |
| PATCH | `/astronauts/{astronaut_id}` | 200, updated profile |
| DELETE | `/astronauts/{astronaut_id}` | 204, no body; 409 when referenced |
| POST | `/health/ingest` | 201, stored-reading array |
| GET | `/health/{astronaut_id}/latest` | 200, newest reading per measurement type |
| GET | `/health/{astronaut_id}/history` | 200, chronological array; type/time filters, limit/offset |
| POST | `/health/{astronaut_id}/analyses` | 201, saved mock/local analysis |
| GET | `/health/{astronaut_id}/analyses` | 200, full saved-analysis array; newest first, limit/offset |
| GET | `/health/{astronaut_id}/analyses/latest` | 200, latest saved analysis; 404 if none |
| GET | `/health/{astronaut_id}/analyses/{analysis_id}` | 200, astronaut-scoped saved analysis |
| POST | `/ai/assistant` | 200, labelled mock or configured-provider response |

Responses use typed Pydantic models. Errors use `detail` as a string or validation
array; DELETE is the deliberate empty-body exception. Keep null anomaly values
distinct from false/zero and show mock provenance. Runtime OpenAPI is at
`/openapi.json` and interactive documentation at `/docs`.

[FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md) provides copyable JSON response
examples, Fetch usage, CORS verification, response ordering, units, error handling,
and pending Member 5 decisions. Tests cover the existing CRUD, ingestion, history,
analysis and assistant APIs; `tests/test_cors.py` adds browser-origin and preflight
checks. Run the full suite with:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
```

The existing 11 real-ML HTTP cases remain part of that suite; install optional
`requirements-ml.txt` to run them without dependency skips.

### Digital Twin status

No Twin endpoint, alert API or approved Twin response contract currently exists.
[TWIN_API_PROPOSAL.md](TWIN_API_PROPOSAL.md) is a backend-local draft for Member 6
covering indicators, baseline/anomaly provenance and explicit alert unavailability.
It is not implemented or added to OpenAPI. Members 5 and 6 must confirm their data
requirements and missing/stale/mock behavior before that shared response is finalized.
