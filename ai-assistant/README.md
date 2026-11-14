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
set LLM_PROVIDER=offline
python -m uvicorn app.main:app --reload
```

Then open:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/api/v1/demo

## Environment variables

```env
LLM_PROVIDER=offline
LLM_MODEL=
LLM_BASE_URL=
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=30
```

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
