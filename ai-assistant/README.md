# ADORA AEGIS AI Assistant

This module contains the Member 3 AI prototype for astronaut health explanation, bounded question answering, and local knowledge retrieval. The implementation is intentionally conservative and demo-friendly: it does not claim medical validation, does not rely on paid APIs by default, and uses synthetic data labels.

## Scope

- Validate ML-style astronaut data before it passes into the assistant.
- Generate deterministic explanations for alerts.
- Support fixed question categories and a safe offline fallback.
- Search local approved knowledge sources with provenance metadata.
- Expose a FastAPI route set for integration and local demo work.

## Quick start

On Windows:

```bat
cd ai-assistant
START_WINDOWS.bat
```

Manual setup:

```bat
cd ai-assistant
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python -m uvicorn app.main:app --reload
```

Then open:

- http://127.0.0.1:8001/docs
- http://127.0.0.1:8001/api/v1/demo

## Environment variables

```env
LLM_PROVIDER=offline
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=
LLM_TIMEOUT_SECONDS=60
LLM_MAX_OUTPUT_TOKENS=600
LLM_MAX_RETRIES=1
```

For the official OpenAI Responses API, set `LLM_PROVIDER=openai` and put a newly generated API key in the ignored local `.env` file. The key must never be placed in frontend code, committed, or pasted into chat. `LLM_PROVIDER=offline` remains the safe default; `LLM_PROVIDER=openai_compatible` and `LLM_PROVIDER=ollama` remain available for existing deployments.

OpenAI API billing is separate from a ChatGPT Plus subscription. Plus provides ChatGPT product access; API usage requires an API Platform account with billing/credits configured and is charged by API usage. See the official [API billing overview](https://help.openai.com/en/articles/9039756-billing-settings-in-chatgpt-vs-platform) and [API billing setup](https://help.openai.com/en/articles/8264644-how-can-i-set-up-prepaid-billing).

To run a live test on the team-safe port after configuring billing and receiving approval:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
$body = @{ astronaut_id = "AST-SYNTHETIC-01"; question = "Introduce yourself as AEGIS and explain how you support astronaut health monitoring. Do not invent sensor readings." } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/api/v1/chat -ContentType "application/json" -Body $body
```

Automated tests use mocks and never make paid API calls. See `OPENAI_CLOUD_VERIFICATION.md` for the evidence report.

## Demo payload

```json
{
  "astronaut_id": "AST-001",
  "timestamp": "2026-11-14T07:00:00Z",
  "metric": "heart_rate",
  "current_value": 110,
  "baseline_value": 72,
  "unit": "bpm",
  "anomaly_detected": true,
  "anomaly_score": 0.87,
  "score_definition": "example_score_not_medical_probability",
  "trend": "increasing",
  "sensor_quality": "good",
  "data_source": "simulated",
  "model_name": "isolation_forest",
  "context": {"activity": "unknown"}
}
```

## API routes

- `GET /api/v1/health`
- `GET /api/v1/demo`
- `POST /api/v1/alerts/explain`
- `POST /api/v1/chat`
- `POST /api/v1/knowledge/search`
- `GET /api/v1/knowledge/status`

## Safety notes

- Prototype data is synthetic and should never be described as live NASA telemetry.
- This code does not provide diagnoses or treatment instructions.
- Score values are not interpreted as medical probabilities unless a documented definition is provided.
- The system must not invent citations, diagnoses, or measurements.

## Testing

```bat
cd ai-assistant
.venv\Scripts\python.exe -m pytest -q
```
