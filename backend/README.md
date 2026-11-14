# Backend

The backend owns the HTTP API boundary. Its initial FastAPI application exposes
a health check so the service can be started and checked before other modules
are integrated.

**Inputs:** HTTP requests. Future sensor endpoints should accept validated JSON
that follows [`docs/data-schema.md`](../docs/data-schema.md).

**Outputs:** JSON responses documented in
[`docs/api-contracts.md`](../docs/api-contracts.md).

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

Only the health endpoint is implemented. No database, sensor ingestion, ML, AI,
or clinical functionality is included yet. No other module is required to start
this server. SQLAlchemy and SQLite setup belong to Phase 2.

The shared health contract is preserved. Before ingestion implementation, resolve
the difference between `docs/data-schema.md` (grouped readings, e.g. `beats/min`)
and the proposed per-measurement format (`bpm`, source and simulation metadata)
with the team lead. The root README's member assignments also differ from the
current backend assignment. These shared files have not been changed.
