# Gemini dashboard chat

Chat is available in **LIVE API MODE**. React calls only the central backend
on port 8000, which forwards the question, astronaut ID and optional selected
analysis summary to Member 3 on port 8002. Only Member 3 holds provider keys.

## Run the services

Use separate PowerShell terminals from the integrated checkout. Install each
module's requirements first. Member 3 includes Google's official `google-genai`
SDK and the OpenAI SDK. Keep credentials in the AI process environment or its
ignored local `.env`; never copy another worktree's `.env` or put keys in Vite.

### AI Assistant

Member 3 has a native `gemini` provider. Configure `GEMINI_API_KEY` privately
before startup, without including its value in commands, source or chat. Set
`GEMINI_MODEL` to a model enabled for your account (the template defaults to
`gemini-2.5-flash`). The remote readiness report does not establish this
machine's credentials or provider availability.

```powershell
$env:LLM_PROVIDER = 'gemini'
$env:LLM_TIMEOUT_SECONDS = '60'
Set-Location ai-assistant
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

GET `http://127.0.0.1:8002/api/v1/health` reports provider/configuration
availability; it does not prove generation or key validity. Offline mode
supports deterministic chat and NASA search, but the backend provider route
deliberately returns 503. No live generation without separate Team Lead approval.

### Backend

```powershell
$env:AI_ASSISTANT_URL = 'http://127.0.0.1:8002/api/v1/assistant/respond'
$env:AI_ASSISTANT_TIMEOUT_SECONDS = '70'
$env:AEGIS_CORS_ORIGINS = '["http://localhost:5173","http://localhost:5175"]'
$env:AEGIS_DATABASE_PATH = Join-Path $env:TEMP 'aegis-gemini-demo.sqlite3'
$env:PYTHONPATH = (Resolve-Path .\ml-engine).Path
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

The URL and timeout above are defaults. Set `AI_ASSISTANT_URL` explicitly blank
to disable the bridge. Legacy `AEGIS_ASSISTANT_URL` (base URL) and
`AEGIS_ASSISTANT_TIMEOUT_SECONDS` work when canonical settings are absent.
The browser cannot choose the provider URL. Redirects and ambient proxies are
disabled for this bridge; connect timeout is at most 5 seconds. Keep configured
timeouts ordered Member 3 < backend < browser (default 60 < 70 < 90 seconds).
Seed synthetic data using the root README and check backend `/health`.
Backend bridge changes require **Member 4 review**.

### Frontend

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
$env:VITE_API_TIMEOUT_MS = '10000'
$env:VITE_ASSISTANT_MODE = 'mock'
Set-Location frontend
npm.cmd run dev -- --host localhost --port 5175
```

Open `http://localhost:5175/`, choose LIVE API MODE, select a synthetic
astronaut, and submit a question. Chat/explanation requests have a 90-second
browser timeout; ordinary reads use the existing 10-second timeout.

`mock` is the safe default. Restart Vite with `VITE_ASSISTANT_MODE=local` for
explicit provider questions after approval. Opening the dashboard, switching
astronauts, polling and running ML never generate cloud requests. Automatic
analysis explanations always request mock mode.

## Provenance, errors and limitations

- Explicit mock replies show **MOCK / OFFLINE RESPONSE**. `is_mock:false` shows
  **REAL PROVIDER RESPONSE**, version, status, data source, analysis context
  and limitations. This contract does not identify Gemini. Confirm service
  configuration and genuine generation before describing an answer as Gemini.
- The synthetic educational/non-diagnostic disclaimer remains visible. Missing
  analysis is unknown; mock and insufficient analysis retain their labels.
- Submitted local-mode failures remain errors: 503 unavailable, 504 timeout,
  502 malformed output/identity mismatch. They never become mock successes.
- Duplicate submissions are blocked. Switching astronaut/mode or unmounting
  cancels pending UI requests and discards stale replies. Cancellation cannot
  guarantee stopping a model request already received by the server.
- The transcript is session-only; no conversation history is persisted or
  forwarded. Each question is independent and limited to 2,000 characters.
- Member 3's schema is unchanged. Provider metadata changes need Member 3
  coordination. Mocked bridge/browser tests do not prove real Gemini.

A live acceptance check requires separate approval for exactly one safe
synthetic educational question, submitted through the local-mode UI. Observe
browser -> backend -> Member 3 -> Gemini -> browser, with the correct astronaut,
nonempty answer/limitations, `is_mock:false`, confirmed Gemini configuration
and successful rendering. Otherwise record **BLOCKED**.
