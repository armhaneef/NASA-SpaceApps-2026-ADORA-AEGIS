# AEGIS AI Assistant

Member 3's separate FastAPI service supplies bounded explanations, local
knowledge retrieval and optional model integration. Data is synthetic and
educational, not NASA astronaut telemetry; no medical validation is claimed.
The dashboard uses backend port **8000**. This service uses **8002** in the
integrated workflow.

## Setup and offline startup on Windows

From the repository root, create the environment only if it does not already
exist, then install this module's declared requirements:

```powershell
Set-Location ai-assistant
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the safe offline service in that terminal:

```powershell
$env:LLM_PROVIDER = 'offline'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

Read-only health and development schemas are at
`http://127.0.0.1:8002/api/v1/health`, `/docs` and `/openapi.json`.
Health reports configuration availability, not key validity or generation.
The historical `START_WINDOWS.bat` uses standalone port 8001; use the explicit
8002 command above for the integrated workflow. An omitted Uvicorn port would
use 8000 and conflict with the backend.

The full [integrated setup](../README.md#run-the-integrated-synthetic-demonstration-on-windows)
and [dashboard chat guide](../docs/gemini-dashboard-chat.md) describe the
backend HTTP bridge and frontend. The browser calls only the central backend.

## Configuration and CORS

Use the AI process environment or an ignored local `ai-assistant/.env` for
private configuration. Never commit a key, paste one into chat, or put one
in Vite. The loader reads module/cwd environment files without overriding
already-set process variables. This correction pass did not open or modify
private environment files.

| Setting | Source-code behavior |
|---|---|
| `LLM_PROVIDER` | Defaults to `offline`; supports `none`, `gemini`, `openai`, `openai_compatible`, `ollama` |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Private Gemini credential and enabled model; source default model is `gemini-2.5-flash`, not a claim of account availability |
| `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL` | Canonical OpenAI settings; legacy `LLM_*` settings remain compatible |
| `LLM_TIMEOUT_SECONDS` | Provider timeout, default 60 seconds |
| `LLM_MAX_OUTPUT_TOKENS`, `LLM_MAX_RETRIES` | Defaults 600 and 1; provider-specific behavior lives in `llm_service.py` |
| `AI_ALLOWED_ORIGINS` | Optional comma-separated explicit HTTP(S) browser origins |

When `AI_ALLOWED_ORIGINS` is omitted, explicit localhost/127.0.0.1 origins on
ports 3000 and 5173 are retained. A configured list replaces those defaults;
whitespace is trimmed, trailing root slashes normalized, and duplicates removed.
Blank values/entries, wildcards, malformed URLs, credentials, non-root paths,
queries and fragments fail with a configuration error at application import.
Unset the variable to use defaults; do not supply an empty value.

For an approved direct browser demo on another port, set an exact origin before
startup, for example:

```powershell
$env:AI_ALLOWED_ORIGINS = 'http://localhost:5173,http://localhost:5175'
```

Credentialed CORS is disabled: these JSON APIs do not use cookie/session
credentials. Backend-to-AI HTTP calls do not depend on browser CORS. CORS is
not authentication; keep this prototype bound to loopback rather than exposing
an unauthenticated model-backed service publicly.

## Mock, stub and provider distinctions

- Backend assistant `mode: mock` is a static labelled placeholder; it never
  calls this service or a model.
- This service's offline chat/alert paths can return deterministic educational
  text. The backend-compatible provider route deliberately returns 503 when
  its provider is unavailable; it does not substitute offline success.
- Controlled tests install fake SDKs, HTTP transports or stub LLMs. A fixture
  with `is_mock:false` or `offline_mode:false` does not prove a real provider.
- Backend `mode: local` means call this local service. A configured Gemini
  provider is remote AI and may require network/account access. Provider keys
  remain here, not in the backend/frontend.

Current full browser-to-Gemini generation is **NOT VERIFIED**. Two previous
integration acceptance attempts returned HTTP 503. Historical component-level
Gemini successes describe earlier verification contexts, not this checkout's
full integration acceptance. Successful health checks do not close that gate.
No real generation is authorized by these setup instructions; obtain separate
approval before any live chat/provider request. See the
[current QA record](../docs/aegis-final-integration-qa.md). Older Member 3 reports
remain historical evidence and do not supersede that integration checkpoint.

## API routes

All paths below use the `/api/v1` prefix:

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Process/configuration health, no generation |
| GET | `/demo` | Synthetic demonstration payload |
| POST | `/alerts/explain` | Deterministic synthetic alert explanation |
| POST | `/chat` | Chat with deterministic/offline or configured-provider behavior |
| POST | `/assistant/respond` | Strict backend-compatible minimal-summary contract |
| POST | `/knowledge/search` | Local approved evidence search |
| GET | `/knowledge/status` | Local evidence inventory |
| GET | `/voice-demo` | Prototype voice UI |
| GET | `/voice/status` | Capability report, not hardware acceptance |
| POST | `/voice/transcribe` | Optional speech recognition |
| POST | `/voice/speak` | Optional speech output |

Schemas are in `app/schemas/`; the backend handoff is documented in
[TEAM_INTEGRATION_STATUS.md](TEAM_INTEGRATION_STATUS.md) as a historical report.
Current bridge behavior is described in
[backend/PHASE5_ASSISTANT.md](../backend/PHASE5_ASSISTANT.md).

## Tests and safety limits

From `ai-assistant`:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
```

Provider-generation tests use mocks/stubs. In this correction pass, an external
QA launcher suppressed private dotenv reads and blocked external/provider
connections, while allowing temporary dotenv fixtures and disposable loopback
HTTP services. See the QA record for actual rerun counts. The suite includes
origin validation, unauthorized preflights, non-credentialed allowed responses
and startup failure for invalid CORS configuration.

Medical-policy and evidence checks reduce risk; they do not guarantee that
model text is factual. Scores are not medical probabilities. Do not invent
measurements or citations, diagnose, prescribe, or use this prototype for
medical or mission decisions. Hardware voice and physical mobile performance
remain separate acceptance work.
