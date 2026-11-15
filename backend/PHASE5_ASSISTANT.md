# Phase 5: assistant adapter and endpoint

This documents the implemented backend bridge to Member 3's existing
`POST /api/v1/assistant/respond` route. The backend owns
validation, context selection and error handling; Member 3 owns assistant content,
medical safety rules, approved knowledge retrieval and provider configuration.

## Endpoint

`POST /ai/assistant` returns 200 for a valid mock or configured-provider response.

```json
{
  "astronaut_id": "AST-AI-DEMO",
  "question": "What does this prototype analysis represent?",
  "mode": "mock"
}
```

The astronaut must already exist. `question` is stripped of surrounding whitespace
and must contain 1–2000 characters. `mode` defaults to `mock`; allowed values are
`mock` and `local`. Unknown fields are rejected. Optional `analysis_id` must be a
positive JSON integer identifying an analysis for that exact astronaut.

Response fields:

| Field | Meaning |
| --- | --- |
| astronaut_id | Requested astronaut identifier |
| answer | Static placeholder or validated provider text |
| assistant_version | Explicit backend mock or provider version |
| is_mock | Always true for backend mock; preserves provider's explicit flag in local mode |
| limitations | Required nonempty list of limitations |
| response_timestamp | Backend UTC response time |
| mode | Requested mock/local mode |
| status | `mock` when `is_mock=true`, otherwise `completed` |
| data_source | `backend_mock` or `configured_local_provider` |
| context | Minimal selected analysis context, or `{"analysis": null}` |

`completed` means the provider returned a structurally valid answer, not that
the content has been medically validated. A provider's own mock result stays
labelled `is_mock=true`, even when reached through local mode. Analysis mock
status and assistant mock status are separate and both remain visible.

Backend mock text is fixed and explicitly says that no assistant is connected,
no question interpretation was performed and no health assessment was made.
It generates no medical advice, uses no AI provider or retrieval system, and
works offline. Neither questions nor responses are saved or logged by this
feature. No conversation table or database migration is needed.

## Context and data minimization

Without `analysis_id`, no saved analysis is automatically selected, even if one
exists. The provider receives only the requested astronaut ID, question and empty
context. With `analysis_id`, the selected analysis summary includes:

- ID, generation and measurement timestamps, source and model version.
- Status, nullable anomaly flag/score, affected measurements and `is_mock`.
- Original ML data-quality details, overall detector method and sensor method,
  or null for backend mock analyses.

This preserves unknown/insufficient-data states and distinguishes sensor baseline
flags from joint-detector results. Scores are not medical probabilities. No
astronaut name, mission profile, arbitrary profile metadata, raw sensor rows,
prepared history, full ML result, or other conversations are forwarded.

Cross-astronaut analysis IDs return 404 before the provider is called. Astronaut
scoping prevents accidental context mixing; it is not authentication. The local
MVP still has no user authorization layer. Request-supplied questions can contain
personal information; approved-provider handling remains Member 3's responsibility.

## Graceful errors

| Status | Meaning |
| --- | --- |
| 404 | Missing astronaut or analysis not belonging to this astronaut |
| 422 | Invalid request, blank/oversized question, invalid mode or analysis ID |
| 503 | Local provider is unconfigured or raised an execution error |
| 504 | Configured provider reported `TimeoutError` |
| 502 | Provider output is malformed or has a different astronaut ID |

Failure responses contain `detail`, not an invented successful answer. Provider
exception messages and raw output are not exposed. No automatic fallback occurs;
the caller can deliberately retry with `mode: "mock"`. Other backend APIs remain
available. The synchronous route runs through FastAPI's worker thread pool.

## Draft integration interface for Member 3

`AIAdapter(provider=callable)` accepts an approved synchronous callable:

```python
def respond(payload: dict) -> dict:
    ...  # Member 3's implementation
```

The payload is JSON-compatible:

```json
{
  "astronaut_id": "AST-AI-DEMO",
  "question": "What does this prototype analysis represent?",
  "context": {"analysis": null}
}
```

The provider must return exactly this shape (limits are in
`app/schemas/assistant.py`):

```json
{
  "astronaut_id": "AST-AI-DEMO",
  "answer": "Provider-owned explanation text.",
  "assistant_version": "member3-version",
  "is_mock": false,
  "limitations": ["Provider-owned uncertainty and limitations."]
}
```

`answer` is a nonempty string up to 12000 characters; version is up to 100;
limitations has 1–20 nonempty strings up to 1000 each. Unknown fields, non-JSON
values and nonfinite numbers are rejected. The backend checks identity and
structure; it cannot certify factual or medical safety from this schema.

Set `AEGIS_ASSISTANT_URL=http://127.0.0.1:8001` to enable the fixed local HTTP
bridge. `AEGIS_ASSISTANT_TIMEOUT_SECONDS` controls its request timeout (default
3 seconds, maximum 30). The URL is configuration only; request data cannot
choose a host. The bridge sends the exact `astronaut_id`, `question`, and
`context` shape above, validates the returned schema and identity, and maps
timeouts/unavailability to safe HTTP errors. `mode: "mock"` remains available
without starting Member 3's service. The bridge does not claim that an offline
or mock assistant performed an explanation.

Member 3's service must run on a separate port because both FastAPI apps
otherwise default to 8000. Its `LLM_PROVIDER=offline` setting does not provide a
non-mock answer; a local model such as configured Ollama is needed for that.

## Verify in PyCharm and /docs

Use `backend/.venv/Scripts/python.exe` as the PyCharm interpreter and `backend`
as the working directory. The bridge uses the Python standard library.
From the terminal at the repository root:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Stop an older server first or let the existing development server reload.
Open http://127.0.0.1:8000/docs and use **Try it out → Execute**:

1. Create a fictional astronaut through **POST /astronauts**:

   ```json
   {
     "astronaut_id": "AST-AI-DEMO",
     "name": "Mira Sen (fictional)",
     "mission_id": "MARS-SIM-01",
     "mission_role": "Engineer"
   }
   ```

   Expect 201; if that ID already exists, reuse it rather than creating it again.
2. Execute **POST /ai/assistant** using the first JSON example. Expect 200,
   an answer beginning `MOCK:`, `is_mock: true`, `status: "mock"`, limitations,
   and `context: {"analysis": null}`. No sensor readings are required.
3. Change mode to `local`. Without `AEGIS_ASSISTANT_URL`, expect 503. With the
   Member 3 service configured but its provider offline, expect a safe 503; no
   successful-looking answer is returned.
4. Submit a whitespace-only question: expect 422. Use an unknown astronaut:
   expect 404. The health endpoint should still return `{"status":"ok"}`.
5. Optionally follow Phase 4 to create an analysis for `AST-AI-DEMO`, add its
   integer `analysis_id` to the mock assistant request, and inspect the returned
   context. A mock analysis must remain marked mock with null anomaly values.
   An analysis ID belonging to a different astronaut returns 404.

Tests use temporary databases and provider stubs, not a real language model. They
exercise offline mock operation, validation, minimal context, mock provenance,
uncertainty, provider mutation isolation, safe errors, OpenAPI, and no database
writes. Real provider content, retrieval, safety behavior and enforced deadlines
remain unverified until a configured local model returns an actual response over
the HTTP bridge.
