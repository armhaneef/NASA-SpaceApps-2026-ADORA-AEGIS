# Gemini dashboard chat

The dashboard chat is available in **LIVE API MODE**. The browser sends
`POST /ai/assistant` requests to FastAPI with the selected synthetic astronaut,
the user's question, and the explicitly selected `mock` or `local` mode. The
backend validates the request and, in local mode, forwards only the permitted
question and optional analysis summary to the AI Assistant service. The browser
never receives or sends the Gemini API key.

## Run the services

Use three terminals from the repository root. Keep Gemini credentials in the
AI Assistant process environment or its local, untracked configuration only.
Do not put a key in frontend variables or commit it.

### 1. AI Assistant with Gemini

The AI Assistant currently uses its OpenAI-compatible provider client for
remote providers; it does not have a Gemini-specific provider name. Gemini's
OpenAI-compatible endpoint can be configured as follows, using a model
currently enabled for the Google AI Studio key:

```powershell
$env:LLM_PROVIDER = 'openai_compatible'
$env:LLM_MODEL = 'gemini-2.5-flash'
$env:LLM_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'
$env:LLM_API_KEY = '<Google AI Studio API key>'
$env:LLM_TIMEOUT_SECONDS = '25'
Set-Location ai-assistant
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

The key above is a placeholder, not a credential. Verify the service reports
`llm_available: true` at `http://127.0.0.1:8002/api/v1/health`. Its health
response reports a provider type and availability, but not the selected model
name.

### 2. Backend

From the repository root, configure the backend's fixed provider URL and
provider-call timeout. The timeout must be long enough for the model response;
the backend limit is 30 seconds.

```powershell
$env:AEGIS_ASSISTANT_URL = 'http://127.0.0.1:8002'
$env:AEGIS_ASSISTANT_TIMEOUT_SECONDS = '30'
$env:AEGIS_CORS_ORIGINS = '["http://localhost:5173","http://localhost:5175"]'
$env:AEGIS_DATABASE_PATH = Join-Path $env:TEMP 'aegis-gemini-demo.sqlite3'
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Seed synthetic astronaut data using the existing adapter instructions in the
root README. Confirm `http://127.0.0.1:8000/health` is available.

### 3. Frontend

Start Vite with local assistant mode. The dashboard API URL remains the backend;
the browser does not call the AI Assistant directly.

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
$env:VITE_API_TIMEOUT_MS = '10000'
$env:VITE_ASSISTANT_MODE = 'local'
Set-Location frontend
npm.cmd run dev -- --host localhost --port 5175
```

Open `http://localhost:5175/`, switch to **LIVE API MODE**, choose a synthetic
astronaut, and ask a question in the assistant panel. Chat requests have a
35-second browser timeout. A completed response with `is_mock: false` is shown
as **REAL PROVIDER RESPONSE** with the reported assistant version and
limitations. The current backend response contract does not identify Gemini by
name, so this UI label confirms only a non-mock provider response. Confirm the
server-side Gemini configuration separately before describing a response as
Gemini-generated.

## Mock and offline behavior

`VITE_ASSISTANT_MODE=mock` is the default and deliberately requests the backend's
fixed mock response. The UI labels these replies **MOCK / OFFLINE RESPONSE**.
Local-mode provider errors remain errors; chat does not silently replace them
with mock output. The existing automatic analysis explanation may explicitly
request a mock fallback and labels it as such.

The AI Assistant's default `LLM_PROVIDER=offline` cannot generate Gemini
responses. If Gemini is unavailable, the AI Assistant health endpoint reports
the configured provider state; local chat returns an error rather than a
success-shaped fallback. The prototype is educational, uses synthetic data,
and does not provide diagnosis or treatment advice.

## Contract and limitations

- The backend chat route is `POST /ai/assistant`; accepted modes are `mock` and
  `local`. `question` is limited to 2,000 characters.
- In local mode, the backend calls the configured
  `POST /api/v1/assistant/respond` endpoint; the URL is fixed by backend
  configuration, not supplied by the browser.
- No conversation history is persisted or forwarded. Each submitted question
  is sent independently; the dashboard only retains the visible transcript in
  the current page session.
- The provider identity/model is not included in the backend chat response.
  Member 3 approval is needed to extend the AI Assistant response contract with
  verified Gemini provider metadata.
- A real Gemini result requires a configured credential and running services.
  Frontend contract tests and backend stub tests do not establish end-to-end
  provider connectivity.
