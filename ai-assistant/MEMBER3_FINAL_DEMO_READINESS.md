# ADORA AEGIS — Member 3 Final Demo Readiness

> **Current checkpoint:** See Section 13 (2026-11-15). Sections 1–12 record earlier audit findings; where they conflict, Section 13 is current and authoritative. Current demo preference is OpenAI Internet AI only.

**Audit date:** 2026-11-15
**Scope:** `ai-assistant/` implementation and read-only compatibility review of the shared backend/frontend. No backend or frontend files were edited. No cloud API call, installation, model download, branch switch, commit, or push was performed.

## தமிழ் சுருக்கம்

- **OFFLINE DEMO VERIFIED:** `127.0.0.1:8001` இல் Uvicorn இயக்கி பார்த்தோம். Offline chat HTTP 200-ஐ `offline_mode: true` உடன் திருப்பியது; NASA local search-லும் முடிவுகள் கிடைத்தன. இது deterministic offline விளக்கம் மட்டுமே; generative AI அல்ல.
- **503 காரணம்:** `LLM_PROVIDER=offline` நிலையில் `/api/v1/assistant/respond` உண்மையான provider பதிலை உருவாக்க முடியாததால் 503 தருவது திட்டமிட்ட நடத்தை. Member 4 backend-இன் `get_ai_adapter()`-லும் Member 3-க்கு HTTP provider இணைப்பு இன்னும் இல்லை.
- **சோதனைகள்:** முழு 63-test suite, PowerShell உருவாக்கிய தற்காலிக test directory மற்றும் test-run-only fixture workaround மூலம் 63 passed, 2 warnings. சாதாரண pytest temp fixture இன்னும் Windows sandbox permission காரணமாக இயங்கவில்லை; test source மாற்றப்படவில்லை.
- **உள்ளூர்/Cloud AI:** `ai-assistant/.env`-ல் OpenAI key இல்லை. Ollama கிடைக்கவில்லை; local model உறுதி செய்யப்படவில்லை. Billing UNKNOWN. எந்த real model பதிலும் கிடைக்கவில்லை; எந்த paid API call-மும் செய்யப்படவில்லை.
- **மற்ற வேலை:** Member 4 provider bridge அமைக்க வேண்டும். Member 5 chatbot UI-ஐ backend `/ai/assistant` endpoint-க்கு இணைக்க வேண்டும். இருவரின் கோப்புகளும் மாற்றப்படவில்லை.

## 1. Repository and branch

- Workspace: `C:\Users\Nuski_Ahamed\ADORA-AEGIS-DEV`
- Branch: `dev`; HEAD `8bc558b7fb1be86fc839f690140f2236ea980270` (`Update AI assistant`)
- Local `dev` equals the locally recorded `origin/dev`. No fetch was performed, so GitHub's latest state is **UNKNOWN**.
- The working tree was clean after the audit and report creation. This report is the only file created by this task.

## 2. Current implementation and findings

**IMPLEMENTED:** FastAPI app, deterministic alert explanations, offline typed chat, OpenAI Responses API path, OpenAI-compatible path, Ollama path, Member 4 provider endpoint, local knowledge search, input/output safety checks, and voice routes.

The provider set in `app/services/llm_service.py` is exactly `offline`, `none`, `openai`, `openai_compatible`, and `ollama`. `openai` uses the official Python SDK's `client.responses.create(...)`; `ollama` posts to `/api/generate` and does not require an API key. Configuration-based availability does not check that a provider is reachable; a generation request is required to prove it.

The existing offline/deterministic features were preserved. No source bug was established that warranted a code change.

## 3. HTTP 503: cause and verification

With `LLM_PROVIDER=offline`, a real local Uvicorn session on `127.0.0.1:8001` produced:

- `POST /api/v1/chat` with a synthetic non-alert question: **HTTP 200**, `offline_mode: true`, `status: "ok"`, bounded offline text.
- `POST /api/v1/knowledge/search` for NASA astronaut sleep: **HTTP 200**, local evidence available, five results.
- `POST /api/v1/assistant/respond` with a synthetic Member 4-shaped request: **HTTP 503**, `{"detail":"Configured local assistant provider is unavailable."}`.

This 503 is intentional: `respond_to_backend()` requires `LLMService.is_available()` and raises `LLMCallError` if the provider is unconfigured/unavailable; the route maps this to 503. It does not fabricate a successful provider answer. Existing tests also verify provider error handling and offline labeling.

The separate backend integration is still incomplete: Member 4's `get_ai_adapter()` returns `AIAdapter()` without a provider callable. Therefore Member 4's `mode: "local"` currently cannot call Member 3, even if Member 3 is running. This is a second blocker distinct from Member 3's offline 503.

## 4. Test results

Fresh exact command `python -m pytest -q -p no:cacheprovider` was attempted. Result: **62 passed, 1 error, 2 warnings**. The only error is setup for `test_dotenv_file_loads_openai_configuration_without_printing_credentials`: pytest cannot scan the existing `C:\Users\Nuski_Ahamed\AppData\Local\Temp\pytest-of-Nuski_Ahamed` directory (`PermissionError: [WinError 5] Access is denied`).

Environment investigation:

- `TEMP` and `TMP` both point to the user's `AppData\Local\Temp`.
- Python `tempfile.gettempdir()` resolves to the same Temp folder; ordinary parent-folder listing and a direct temporary-file write succeeded.
- The existing per-user pytest subdirectory itself denies access/listing. A pytest-selected temp directory also could not be traversed/cleaned by this process. No system ACLs or global settings were changed.
- The affected test uses pytest `tmp_path`, writes a temporary `.env`, and starts a subprocess. The test body is valid, but pytest/Python-created temporary folders are inaccessible to the sandbox after creation. No test-code defect was demonstrated.

The full suite was then executed through `pytest.main(["-q", "-p", "no:cacheprovider"])` with a run-only fixture plugin providing the same `tmp_path` as a fresh PowerShell-created directory under TEMP. Result: **63 passed, 2 warnings in 1.99s**. The dotenv test body ran and passed; no test source was modified. A separate exclusion run returned **62 passed, 1 deselected, 2 warnings**. Warnings: Starlette/httpx TestClient deprecation and SpeechRecognition's `aifc` deprecation.

**Result interpretation:** All 63 tests passed under the safe test-only temp fixture workaround. The unmodified exact pytest command still encounters the sandbox permission error before it can complete normally. Do not hide that distinction when reporting the test result.

Coverage in the passing suite includes alert explanation, heart rate/SpO₂/temperature scenarios, missing/insufficient data, safety/injection, local knowledge/citation checks, provider failures, voice route/service behavior, and backend-provider contract tests. Voice tests mock hardware; no physical microphone/speaker was tested.

## 5. Local provider availability

**BLOCKED:** `ollama` was unavailable on PATH, and `http://127.0.0.1:11434/api/tags` was not reachable. Since the executable is unavailable, an installed model could not be listed; model availability is **UNKNOWN**. No Ollama installation or model download was attempted.

## 6. OpenAI cloud configuration

**IMPLEMENTED, NOT CONFIGURED/VERIFIED:** Official Responses API client code and SDK dependency are present. No `OPENAI_API_KEY` was set in this process and no `ai-assistant/.env` exists. No model is selected in the current environment. Billing/credits status is **UNKNOWN**. No live or billable request was made. A cloud response would demonstrate **REAL CLOUD AI**, not the Team Leader's **REAL LOCAL AI** requirement; Team Leader acceptance of cloud as an alternative is **NEEDS APPROVAL**.

Current secret check: `OPENAI_API_KEY` configured in `ai-assistant/.env` = **NO**. To configure privately, copy `.env.example` to `.env`, replace its placeholder locally using a text editor, confirm API billing/credits in the account, then restart Uvicorn. Never paste the key into chat or commit `.env`; `.gitignore` excludes it. Do not send a live request until the user explicitly approves the potentially billable test.

## 7. Real model response evidence

- **REAL LOCAL LLM VERIFIED:** No.
- **REAL CLOUD LLM VERIFIED:** No.
- The mocked provider tests prove request/response handling only; they do not prove model generation.
- A successful provider generation in the Member 3 bridge returns `is_mock: false`. Safety refusals may return a deterministic response marked `is_mock: true`. Unavailable provider returns 503 without an assistant success body.

Minimal safe synthetic request to prove a real provider response after approved setup:

```json
{
  "astronaut_id": "SYNTHETIC-ASTRONAUT-001",
  "question": "Briefly describe what this synthetic demo request says about the data provided.",
  "context": {"analysis": null}
}
```

Only classify the result as real generation when it returns HTTP 200, a nonempty `answer`, `assistant_version`, nonempty `limitations`, and `is_mock: false`. `is_mock: true`, mocked test output, offline chat, or HTTP 503 is not proof of generation.

## 8. Offline demo

**OFFLINE DEMO VERIFIED:** Yes, for service behavior. A real local Uvicorn process was started on `127.0.0.1:8001`; chat returned HTTP 200 with `offline_mode: true`, and the local NASA knowledge search returned five results. The process was stopped after verification.

Use the label **“OFFLINE DETERMINISTIC DEMONSTRATION”** in any presenter notes. This demo shows bounded explanation and local evidence retrieval; it does not demonstrate a generative model. It does not prove Member 4 or React integration.

### Windows PowerShell startup and demo

In PowerShell, from the current checkout:

```powershell
Set-Location 'C:\Users\Nuski_Ahamed\ADORA-AEGIS-DEV\ai-assistant'
$env:LLM_PROVIDER = 'offline'
python -B -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

In a second PowerShell window, demonstrate bounded offline chat:

```powershell
$body = @{ astronaut_id = 'SYNTHETIC-ASTRONAUT-001'; question = 'Explain the synthetic sleep schedule.' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/api/v1/chat' -ContentType 'application/json' -Body $body
```

Demonstrate local NASA evidence search:

```powershell
$body = @{ query = 'NASA astronaut sleep' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/api/v1/knowledge/search' -ContentType 'application/json' -Body $body
```

For a deterministic alert explanation, use `POST /api/v1/alerts/explain` with a synthetic record containing `astronaut_id`, `timestamp`, `metric`, `current_value`, `baseline_value`, `unit`, `anomaly_detected`, `anomaly_score`, `score_definition`, `trend`, `sensor_quality`, `data_source`, `model_name`, and `context`. Clearly label all values synthetic. The `POST /api/v1/assistant/respond` endpoint is expected to return 503 while offline; do not present that as model output.

## 9. Member 4 technical handoff

### Contract

- **URL:** `http://127.0.0.1:8001/api/v1/assistant/respond`
- **Method:** `POST`, JSON request, synchronous response.
- **Request fields:** `astronaut_id`, `question`, and `context.analysis` (analysis may be null; when present it is a validated summarized analysis, not raw sensor rows).

Safe synthetic example (illustrative request only):

```json
{
  "astronaut_id": "SYNTHETIC-ASTRONAUT-001",
  "question": "Explain this synthetic analysis and its limitations.",
  "context": {
    "analysis": {
      "analysis_id": 17,
      "analysis_timestamp": "2026-01-01T01:41:00Z",
      "measurement_timestamp": "2026-01-01T01:40:00Z",
      "status": "normal",
      "is_mock": false,
      "anomaly_detected": false,
      "anomaly_score": 0.18,
      "affected_measurements": [],
      "model_version": "2.0.0",
      "data_source": "synthetic_example",
      "data_quality": {"status": "valid", "errors": {}},
      "detector_method": "personalized_baseline_deviation",
      "sensor_method": "personalized_baseline_deviation"
    }
  }
}
```

- **Successful response fields:** `astronaut_id`, nonempty `answer`, `assistant_version`, boolean `is_mock`, and nonempty `limitations`.
- **Status handling:** 200 means a valid provider response or a deterministic safety refusal. Check `is_mock`; only a successful provider generation is `false`. 400 is request/policy validation; 422 is schema validation; 503 means provider unavailable. The backend should map provider transport timeouts to its expected 504 path.
- **Required configuration:** Run Member 3 on port 8001 with a working provider. For Ollama, configure `LLM_PROVIDER=ollama`, `LLM_MODEL=<already installed model>`, and `LLM_BASE_URL=http://127.0.0.1:11434`; Ollama needs no key. Do not configure until a model exists. For cloud OpenAI, credentials/billing and an approved live request are separately required.

### Member 4 changes and bridge test

Member 4 must configure `backend/app/services/ai_adapter.py:get_ai_adapter()` to provide a synchronous HTTP callable that POSTs the validated JSON to the URL above, uses a bounded timeout (for example 30 seconds), converts `httpx.TimeoutException` to built-in `TimeoutError`, raises for non-2xx responses, parses JSON, and lets `AIAdapter` validate the response. Keep the existing astronaut scoping and summary-only payload.

Start both services (Member 4 on port 8000; Member 3 on 8001), then POST to Member 4 `http://127.0.0.1:8000/ai/assistant` with `mode: "local"` and a real backend-created synthetic astronaut ID. Optionally include an explicitly selected `analysis_id`. Confirm successful response metadata, `is_mock`, limitations, and timeout/unavailable handling. In current source the provider is not wired, so this bridge test is **BLOCKED** until Member 4 makes that change.

## 10. Member 5 frontend handoff

Current `dev` has no `frontend/src/AiChatPanel.jsx`, `frontend/src/chatApi.js`, or `frontend/tests/chatApi.test.js`; `frontend/src/App.jsx` does not mount an AI chat or call `/ai/assistant`. Only `dev` and `origin/dev` were present in the local branch listing; no separate local feature branch with those files was found. No frontend files were modified and no browser integration was claimed.

Member 5 should connect a question UI to the central backend `POST http://127.0.0.1:8000/ai/assistant`, not call Member 3 directly. Show loading, network/503/504 errors, answer, `is_mock`, limitations/uncertainty, and simulated provenance distinctly. Keep deterministic/mock output visibly separate from real model output. The backend default CORS origin includes `http://localhost:5173`; verify the actual browser origin. Use a running browser test before claiming frontend integration.

## 11. Remaining blockers and classifications

| Requirement | Classification | Status |
|---|---|---|
| Member 3 deterministic/offline behavior | IMPLEMENTED / TESTED | Local service behavior verified; 62 suite tests pass when the one temp-fixture test is excluded. |
| Full AI test suite | BLOCKED | One `tmp_path` test cannot set up due Temp subdirectory access denial; no source test bug identified. |
| Real Ollama/local model answer | BLOCKED / NEEDS APPROVAL | Ollama unavailable; model not listed. Install/download only after explicit approval. |
| Real OpenAI answer | BLOCKED / NEEDS APPROVAL | No API key configured; billing unknown; no paid call made. |
| Member 4 HTTP provider bridge | BLOCKED | Backend provider factory is unconfigured and backend code was not modified. |
| React AI chat | BLOCKED | Chat component/client/tests absent from current branch; Member 5 owns changes. |
| Offline deterministic demo | OFFLINE DEMO VERIFIED | Uvicorn chat and local knowledge search returned successful responses. |
| Reviewed integration to `dev` | NEEDS REVIEW | No Member 3 source fix was needed; this task created only this report. Review report and decide integration steps before any commit/push. |

## 12. Final readiness

**PARTIALLY READY** for a clearly labelled offline deterministic demo. **NOT READY** for a real local-model demo, real cloud-model demo, Member 4 non-mock backend integration, or React AI chat demo. The safest presentable path is the offline demo above with synthetic values and explicit offline labeling.

## 13. Current OpenAI Cloud Setup and Secure-Key Checkpoint — 2026-11-15

### A. Workspace and Git

- Workspace: `C:\Users\Nuski_Ahamed\ADORA-AEGIS-DEV`; branch `dev`; HEAD `8bc558b7fb1be86fc839f690140f2236ea980270`.
- `ai-assistant/.env` is ignored by `ai-assistant/.gitignore`; Git does not track it.
- Current untracked Member 3 files: this report and `scripts/set_openai_key.ps1`. No backend or frontend changes, commits, merges, or pushes.

### B. Files and secret handling

- Created `scripts/set_openai_key.ps1`, a hidden `Read-Host -AsSecureString` helper. It contains no API key, validates a plausible `sk-` format, removes prior canonical and legacy key assignments without printing them, then writes one `OPENAI_API_KEY` entry. It preserves other `.env` lines and reports only `CONFIGURED: YES` or `CONFIGURED: NO` after input.
- Confirmed the current canonical `OPENAI_API_KEY` is empty. A nonempty legacy `LLM_API_KEY` entry was found and removed without displaying its value because code could use it as an OpenAI fallback. No key from chat was reused.
- Current `.env` non-secret settings: `LLM_PROVIDER=openai`, `OPENAI_MODEL=gpt-4o-mini`, `OPENAI_BASE_URL=https://api.openai.com/v1`. Key is **NOT YET CONFIGURED**.

### C. OpenAI implementation

**IMPLEMENTED:** `openai` uses the official OpenAI SDK `client.responses.create(...)`; installed SDK version `1.109.1`. Default timeout is 60 seconds, output cap 600 tokens, configured retry default 1 (bounded to 2), parses nonempty `output_text`, and sets `store=False`. Current source configuration loads successfully. With key absent, provider availability is false and offline fallback remains enabled. Configuration status is not proof of network reachability or key validity.

Existing offline explanation, NASA local retrieval, safety checks, simulated-health context, and voice code were preserved. No Ollama was installed or used.

### D. Tests and offline behavior

- Full Member 3 suite: **63 passed, 2 warnings** (Starlette/httpx TestClient deprecation; SpeechRecognition `aifc` deprecation). The dotenv test normally sees the module `.env` before its own fixture; for this run only, `.env` was moved aside, the suite used a PowerShell-created temp folder through a test-only `tmp_path` fixture, then `.env` was restored unchanged. No test source was changed and no live API request was made.
- Safe API checks with the configured provider but blank key: `POST /api/v1/chat` = **200**, `offline_mode=true`; `POST /api/v1/assistant/respond` = **503** for an allowed synthetic question. This is expected until the new private key is entered.
- PowerShell helper parses successfully. Its interactive key prompt was not invoked during this audit.

### E. API and live-test status

- **CONFIGURED:** Provider/model/base URL and official SDK load.
- **TESTED:** Mocked/config tests pass; offline behavior remains functional.
- **REAL CLOUD AI VERIFIED:** No. No OpenAI request was sent; no HTTP status, generated answer, or `is_mock:false` evidence exists.
- **BLOCKED / NEEDS APPROVAL:** Private new rotated key has not yet been securely entered; billing/credits remain unconfirmed; port 8001 is free (FastAPI is not running).
- The previously exposed key must be revoked at `https://platform.openai.com/api-keys`. API billing/credits are separate from ChatGPT subscriptions; check `https://platform.openai.com/settings/organization/billing/overview`. Do not provide credit-card details in chat.

### F. Secure entry command

Run this single command in the VS Code integrated PowerShell terminal. The child PowerShell's execution-policy bypass is process-only; it does not change global Windows settings. The key is entered in a hidden prompt, not in command arguments or chat:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Nuski_Ahamed\ADORA-AEGIS-DEV\ai-assistant\scripts\set_openai_key.ps1"
```

Expected final helper output is only `CONFIGURED: YES` or `CONFIGURED: NO`. After successful entry, recheck the file/runtime config and ask the user to confirm usable API billing/credits before any live request.

### G. Future one-request test — NOT RUN

After secure entry, billing confirmation, and separate explicit approval, run exactly one request against `POST http://127.0.0.1:8001/api/v1/assistant/respond` with this safe synthetic body:

```json
{
  "astronaut_id": "SYNTHETIC-ASTRONAUT-001",
  "question": "Briefly describe what this synthetic demo request says about the data provided.",
  "context": { "analysis": null }
}
```

Only count genuine cloud generation when HTTP 200 returns a nonempty `answer`, `assistant_version`, nonempty `limitations`, and `is_mock:false`. A safety refusal (`is_mock:true`), mocked test, offline text, or 503 is not a real-model success. No application-level retries should be added for this one test.

### H. FastAPI start command

Port 8001 was free at this checkpoint. After secure key entry, start from `ai-assistant/`:

```powershell
Set-Location 'C:\Users\Nuski_Ahamed\ADORA-AEGIS-DEV\ai-assistant'
python -B -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

`GET /api/v1/health` reports provider/configuration availability; it does not prove a successful OpenAI response. Do not POST the live test until the required approval.

### I. Member handoffs

- **Member 4:** Configure backend `get_ai_adapter()` to POST its validated summary to `http://127.0.0.1:8001/api/v1/assistant/respond`, use a bounded timeout, map `httpx.TimeoutException` to `TimeoutError`, raise on non-2xx, and validate the response. Test backend `POST http://127.0.0.1:8000/ai/assistant` with `mode:"local"`; distinguish `is_mock`, 503, and timeout. Backend bridge is not currently connected.
- **Member 5:** Current checkout lacks the React chat component/client/tests. Connect UI only to central backend `POST http://127.0.0.1:8000/ai/assistant`; show loading, errors, answer, mock flag, limitations, and simulated-data disclosure. Never put the OpenAI key in React/Vite. Frontend integration is not verified.

### J. Git and final checkpoint

`.env` remains ignored; the helper and report are untracked Member 3 artifacts. No source implementation files changed. Current classification: **PARTIALLY READY** for offline demo; **NOT READY** for a real cloud demo until the user enters the new key, confirms billing/credits, the server starts, and the separately approved one-request test succeeds.


## 14. Current Gemini and team-integration checkpoint (2026-11-15)

This section is the authoritative current checkpoint and supersedes earlier OpenAI-only or port-8001 status above. No API key values are recorded here.

### Member 3 service

- Gemini Developer API is selected with `LLM_PROVIDER=gemini`; current model is `gemini-3.5-flash-lite`; `google-genai` 2.34.0 uses API `v1beta` with `vertexai=False`.
- The user confirmed that the Google AI Studio project associated with the configured key is on Free Tier with paid billing disabled. Google documents Standard Free Tier input/output as free for this model; no billing/account settings were changed.
- Two separately authorized live chat checks to `POST http://127.0.0.1:8002/api/v1/chat` have each returned HTTP 200, nonempty provider text, and `offline_mode=false`; each test made one request. They used synthetic astronaut context; no model output or sensor readings are treated as real telemetry. No further live generation is authorized without separate approval.
- `/api/v1/chat` uses the `ChatRequest` contract (`astronaut_id`, `question`; optional `session_id`, `include_context`, `conversation_history`, `ml_context`) and returns `answer`, evidence/source metadata, uncertainty and `offline_mode`.
- `/api/v1/assistant/respond` is the Member 4 provider contract. It accepts `{astronaut_id, question, context: {analysis}}` and returns `{astronaut_id, answer, assistant_version, is_mock, limitations}`. A real configured provider answer is `is_mock:false`; deliberate policy refusals are labelled mock. Provider failures return a generic HTTP 503 without raw provider details.
- Both routes use the same configured `LLMService`; Gemini dispatch goes through the Google Gen AI SDK. The backend-compatible route was verified with mocked Gemini tests; it has not been live-called.
- Safety prompts prohibit invented NASA citations, diagnoses and unsupported measurements; local RAG supplies only verified entries. Input policy rejects diagnosis/treatment/prescription requests. Model prompts and these checks reduce risk but cannot guarantee that generative text will never hallucinate. Review answers and cited sources before operational use.
- Offline fallback, OpenAI provider code, local NASA retrieval, explainable synthetic alerts and voice prototype remain in place.
- Current service port is 8002. The invalid proxy (`127.0.0.1:9`) is bypassed only in the service process with `NO_PROXY`/`no_proxy` containing `generativelanguage.googleapis.com`. TLS verification remains enabled; Windows/global proxy and security settings are unchanged.

### Test record

- Full Member 3 test suite after adding mocked Gemini backend-contract and sanitized-failure coverage: **69 passed, 2 warnings, 0 failures, 0 skipped, 0 deselected**.
- The Windows sandbox could not enumerate pytest-created temporary directories. For the run, a temporary pytest fixture used a PowerShell-created directory, the ignored local `.env` was moved aside only while the dotenv isolation test ran, and it was restored immediately afterward. No test made a live provider call; `.env` was not edited.
- Warnings: Starlette `TestClient`/httpx deprecation and SpeechRecognition `aifc` deprecation.

### Member 4 handoff (backend owner)

The current `backend/app/services/ai_adapter.py:get_ai_adapter()` returns an unconfigured `AIAdapter()`; therefore `mode:"local"` does not yet bridge to Member 3. Backend `mode:"local"` means call the local FastAPI service; Gemini itself remains remote Internet AI.

Configure an approved synchronous provider in the backend factory to POST to `http://127.0.0.1:8002/api/v1/assistant/respond` (prefer an `AI_ASSISTANT_URL` environment setting with that development default). Forward only the validated payload:

```json
{
  "astronaut_id": "SYNTHETIC-ASTRONAUT-001",
  "question": "Explain this synthetic analysis; preserve unknown values and do not diagnose.",
  "context": { "analysis": null }
}
```

Validate the response against the backend's existing `AssistantProviderResponse` contract:

```json
{
  "astronaut_id": "SYNTHETIC-ASTRONAUT-001",
  "answer": "...",
  "assistant_version": "member3-ai-assistant-0.1.0",
  "is_mock": false,
  "limitations": ["...", "..."]
}
```

Use synchronous `httpx.post` with a bounded timeout longer than Member 3's 60-second provider timeout (for example 70 seconds, with a shorter connect timeout). Convert `httpx.TimeoutException` to `TimeoutError` so the current adapter returns 504. Raise on every non-2xx response; the adapter returns a safe 503. Return decoded JSON and let the existing strict backend response model reject malformed fields (502). Do not log prompts, analysis payloads, credentials, or raw provider bodies. Preserve explicit `mode:"mock"`; use `mode:"local"` only after the bridge is configured. Test the bridge with `httpx.MockTransport` or an equivalent fake, including success, 503, timeout, invalid JSON/schema, astronaut mismatch and mock-vs-real flags. Never send Gemini keys from backend; only Member 3 holds the provider key.

### Member 5 handoff (frontend owner)

The current React dashboard has a static ?AEGIS DEMO EXPLANATION / Threshold context? panel in `frontend/src/App.jsx`, but no chat component, chat API client, or chat tests. Its current text says that no backend alert service is connected. Replace/extend that panel with a chat form that calls only the central backend `POST http://127.0.0.1:8000/ai/assistant`; do not call Google directly and do not add any Gemini/OpenAI key to Vite variables.

Send `astronaut_id`, `question`, `mode:"local"`, and optionally a selected `analysis_id`; do not invent analysis IDs. Display the returned `answer`, `is_mock`, `assistant_version`, `limitations`, `status`, and selected `context.analysis` (including its `is_mock`, `status`, and data source). Show loading, validation/provider errors, a visible mock label when `is_mock:true`, simulated-data disclosure, and non-diagnostic disclaimer. A missing or insufficient analysis must remain ?unknown/insufficient?; never render it as normal. Add frontend tests for successful real-labelled and mock responses, loading, HTTP error/timeout, no analysis, and disclaimer. Keep backend errors distinct from mock success.

### Safe staged integration checklist

1. In a dedicated PowerShell terminal, set process-only `NO_PROXY`/`no_proxy` for `generativelanguage.googleapis.com`, then start `python -m uvicorn app.main:app --host 127.0.0.1 --port 8002` from `ai-assistant/`. Check port availability first; do not stop port 8000 or 8001 services.
2. GET `http://127.0.0.1:8002/api/v1/health`; this verifies configuration only, not a model response.
3. Start backend on 8000 and verify its `/health`; run mocked backend bridge tests first. Verify `mode:"mock"` is labelled mock and configured `mode:"local"` reaches Member 3 in a mocked transport test.
4. Start React with `npm run dev -- --host 127.0.0.1`, open the dashboard and verify loading, error and mock states using mocked backend responses.
5. Do not claim full-stack Gemini success until the real bridge and UI path have been explicitly approved and observed. No additional live request is included in this checkpoint.

### Current Git checkpoint

Branch is `dev`; no commit, push or branch switch was made. Existing untracked `.vscode/settings.json` and `ai-assistant/MEMBER3_FINAL_DEMO_READINESS.md` are preserved. The report itself remains untracked until reviewed. Backend and frontend were inspected read-only.
