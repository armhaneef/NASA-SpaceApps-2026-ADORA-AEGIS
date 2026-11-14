# ADORA AEGIS — Ollama Live Verification

**Verification date:** 2026-11-14
**Project:** `C:\Users\Nuski_Ahamed\NASA-SpaceApps-2026-ADORA-AEGIS\ai-assistant`
**Branch:** `dev`
**Python:** 3.14.3 (`C:\Users\Nuski_Ahamed\AppData\Local\Programs\Python\Python314\python.exe`)

## A. Environment

| Check | Result | Evidence |
|---|---|---|
| Ollama installed | **NO** | `ollama` was not found on PATH or the common Windows install path. |
| `ollama --version` | **BLOCKED** | Actual PowerShell-compatible execution exited 1: `'ollama' is not recognized as an internal or external command, operable program or batch file.` |
| `ollama list` | **BLOCKED** | Actual execution exited 1 with the same command-not-recognized output. |
| Model available | **NO / UNKNOWN** | `ollama list` could not run because Ollama is not installed or not on PATH. No model was downloaded. |
| Ollama server reachable | **NO** | GET `http://127.0.0.1:11434/api/tags` failed with Windows connection refused (`WinError 10061`). |
| Existing `.env` | **NO** | No `ai-assistant/.env` file exists. `.env` is ignored by Git. |
| Current runtime configuration | **offline** | No Ollama process/model/configured environment was available when checked. No credentials were printed. |
| Git state | **dev, clean at start** | The verified code was already on `origin/dev`; this task made no app-code edits, commit, or push. |

## B. Code Review and Changes

The existing Ollama implementation is present in `app/services/llm_service.py`:

- Ollama does not require `LLM_API_KEY` when a model name is configured.
- It posts to `<LLM_BASE_URL>/api/generate`, with `stream: false`, the configured model, and parses the JSON `response` field.
- Timeout, HTTP connection/status, and invalid response paths raise `LLMCallError`; the existing offline fallback remains available for regular typed chat.
- `app/core/config.py` loads a local `.env` when `python-dotenv` is installed; `python-dotenv` is in `requirements.txt`.
- The Member 3 provider endpoint is `POST /api/v1/assistant/respond`. It expects a validated astronaut ID, question, and Member 4's summarized analysis context. On successful configured generation it returns `is_mock: false`; when no provider is configured, it returns HTTP 503 rather than pretending a generation succeeded.

**Files changed for this live-test task:** only this verification report. No Ollama config was written, because Ollama is unavailable. No model was downloaded without approval.

## C. Automated Tests

Ran the full suite from the actual `ai-assistant` folder with Python 3.14.3:

```text
40 passed, 2 warnings in 4.63s
```

Failures: **0**. Skips: **0**. Warnings: the existing Starlette/httpx TestClient deprecation and SpeechRecognition `aifc` deprecation. These automated tests include mocked provider/voice tests; they are not evidence of live Ollama generation.

## D. Direct Live Ollama Test

| Check | Result |
|---|---|
| API reachable | **NO** |
| Model installed | **NO / UNKNOWN** |
| Direct real `/api/generate` response | **BLOCKED** |
| HTTP status | No HTTP response; Ollama listener was refused |
| Model name / generated text | Not available; no request could be made |
| Connection error | `WinError 10061`, connection refused |
| Timeout | Not reached; connection was refused before a request could complete |

No mocked response is counted as a live pass. No request was made to a cloud provider.

## E. AEGIS-to-Ollama Test

- AEGIS-to-Ollama response: **BLOCKED**. Ollama is not installed/running, there is no installed model, and the current process configuration is offline.
- Real model response returned: **NO**.
- Offline fallback used in a real generation request during this check: **NO request was made**. Current app configuration/status is offline; this is not a successful model response.
- Safety tests: **PASS in the automated suite**, but no real-model safety behavior was measured.

After Ollama is installed and the model is approved/downloaded, the real AEGIS test should use the existing route and response schema below. Do not mark this row as PASS until the response contains generated text and `is_mock: false`.

## F. Voice Test

- Typed chat and voice-service logic: covered by the full suite; fake recognizer/TTS calls are used by tests.
- Voice HTTP route plumbing: previously checked with device methods stubbed; that does not verify physical devices.
- Microphone hardware / browser permission: **NOT TESTED**.
- Speaker playback: **NOT TESTED**.

## G. Exact Windows Steps Still Required

### 1. Install Ollama and verify the command

Install Ollama for Windows from the official download page: `https://ollama.com/download/windows`. After installation, open a **new** PowerShell window and run:

```powershell
ollama --version
ollama list
```

If PowerShell still says `ollama` is not recognized, restart the terminal or repair the Ollama installation/PATH. Start the Ollama app/service. If needed, use a separate terminal for:

```powershell
ollama serve
```

### 2. Download the chosen model only after your approval

The suggested small demo model is `llama3.2:1b`. The command below downloads model data; it was **not run** during this verification:

```powershell
ollama pull llama3.2:1b
ollama list
Invoke-RestMethod 'http://127.0.0.1:11434/api/tags'
```

### 3. Configure and start the AEGIS AI service

From the `ai-assistant` folder, create the ignored local `.env` with these non-secret settings:

```powershell
cd C:\Users\Nuski_Ahamed\NASA-SpaceApps-2026-ADORA-AEGIS\ai-assistant
@'
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:1b
LLM_BASE_URL=http://127.0.0.1:11434
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=120
'@ | Set-Content -Encoding ascii .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Port 8001 keeps this service separate from Member 4's backend, which normally uses 8000. `.env` is ignored; do not commit it.

### 4. Send a direct real Ollama request

In another PowerShell window:

```powershell
$ollamaBody = @{
  model = 'llama3.2:1b'
  prompt = 'Introduce yourself as the AEGIS astronaut health assistant. State that all example health data is simulated and that you do not diagnose.'
  stream = $false
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri 'http://127.0.0.1:11434/api/generate' `
  -ContentType 'application/json' `
  -Body $ollamaBody
```

Record the actual response's `model`, `response`, and `done` fields. This is the direct live-model gate; it must return real text before proceeding.

### 5. Send an AEGIS assistant request through the implemented endpoint

```powershell
$aegisBody = @{
  astronaut_id = 'SYNTHETIC-ASTRONAUT-001'
  question = 'Explain this synthetic analysis and its limitations.'
  context = @{ analysis = @{
    analysis_id = 17
    analysis_timestamp = '2026-01-01T04:01:00Z'
    measurement_timestamp = '2026-01-01T04:00:00Z'
    status = 'normal'
    is_mock = $false
    anomaly_detected = $false
    anomaly_score = 0.18
    affected_measurements = @()
    model_version = '2.0.0'
    data_source = 'synthetic_example'
    data_quality = @{ status = 'valid'; errors = @{} }
    detector_method = 'personalized_baseline_deviation'
    sensor_method = 'personalized_baseline_deviation'
  } }
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post `
  -Uri 'http://127.0.0.1:8001/api/v1/assistant/respond' `
  -ContentType 'application/json' `
  -Body $aegisBody
```

A true live pass requires HTTP 200, model-generated `answer`, matching astronaut ID, and `is_mock: false`. If this returns 503, check the API service's `.env`, restart Uvicorn, verify `/api/tags`, and test the direct Ollama request first. No answer style alone can prove model provenance.

## H. Remaining Blocker

The current blocker is external setup, not an observed Ollama-code failure: Ollama is absent/unavailable, the model is not confirmed downloaded, and `127.0.0.1:11434` refuses connections. Install Ollama and run `ollama pull llama3.2:1b` manually after approving the download. Then rerun sections D and E and update this report only from those actual results.
