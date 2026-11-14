# Backend

The backend owns the HTTP API boundary. Its initial FastAPI application exposes
a health check so the service can be started and checked before other modules
are integrated.

**Inputs:** HTTP requests. Future sensor endpoints should accept validated JSON
that follows [`docs/data-schema.md`](../docs/data-schema.md).

**Outputs:** JSON responses documented in
[`docs/api-contracts.md`](../docs/api-contracts.md).

**Run locally (from the repository root):**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload
```

Only the health endpoint is implemented. No database or clinical functionality
is included yet.
