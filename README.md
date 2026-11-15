# ADORA – AEGIS

**AI-powered astronaut health monitoring, powered by VitalTwin**

ADORA – AEGIS is a NASA Space Apps Challenge 2026 prototype exploring how
multi-sensor health data, personalized baselines, anomaly detection, an
AI-assisted explanation layer, and an interactive digital twin could be brought
together in a modular application.

> **Prototype notice:** This repository is a software foundation, not a medical
> device or clinical decision-support system. Included sensor data is synthetic
> and illustrative only. It is not NASA data, does not represent a real
> astronaut, and has not been clinically validated.

## Prototype capabilities

- Ingest and validate clearly identified synthetic sensor readings.
- Prepare sensor data for downstream analysis and personalized baselines.
- Explore anomaly-detection models and communicate their outputs with context.
- Provide a safety-conscious health assistant that explains prototype outputs.
- Visualize status in an interactive astronaut digital twin.
- Keep each module independently developable through shared schemas and API
  contracts.

The repository includes a React/Three.js dashboard with an explicitly labelled
demo mode and a separate live API mode, a synthetic data generator and backend
adapter, a FastAPI/SQLite API, a local anomaly-analysis module, and a safety-
conscious assistant service. Local ML and assistant-provider modes require the
setup below; the frontend does not silently replace missing services with real
results.

## Technology stack

| Area | Foundation / planned technology |
|---|---|
| Backend API | Python, FastAPI, SQLAlchemy, SQLite |
| Data engine | Standard-library synthetic generator and backend adapter |
| ML engine | Python, personalized baseline analysis and optional Isolation Forest |
| AI assistant | Separate FastAPI service with bounded explanations and optional local model |
| Frontend | React, Vite, Three.js and Recharts |
| Digital twin | GLB anatomical model and React Three Fiber visualization |

## Six-member team responsibilities

These are role assignments, not named team members. Keep module ownership
separate and integrate through the documented JSON schema and API contracts.

| Member | Primary responsibility | Integration deliverable |
|---|---|---|
| 1 | Synthetic data | Generator, fixtures, provenance, and backend adapter |
| 2 | ML engine | Baseline and anomaly-detection implementation |
| 3 | AI assistant and safety | Explanations, bounded responses, and safety rules |
| 4 | Backend and API | FastAPI endpoints, storage, and module adapters |
| 5 | Frontend | Dashboard, API client, and 3D visualization |
| 6 | Digital twin and docs | Anatomical asset, scientific methodology, and integration review |

The team should agree on schema and interface changes before merging module
work. Do not place credentials, real personal health data, or unreviewed
scientific/clinical claims in this repository.

## Repository layout

```text
frontend/       Frontend module boundary
backend/        FastAPI application
data-engine/    Synthetic-data and preprocessing boundary
ml-engine/      Model and evaluation boundary
ai-assistant/   Assistant, explanation, and safety boundary
digital-twin/   Visualization components and asset boundary
data/           Shared sample data (synthetic only)
docs/           Architecture and interface contracts
tests/          Cross-module and backend tests
```

See each module's README and the documents in `docs/` before integrating work.

## Run the integrated synthetic demonstration on Windows

Use three PowerShell terminals from the repository root. These commands isolate
the run in a separate SQLite file under `$env:TEMP`; they do not write to the
project database.

### One-time environment setup

```powershell
py -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt -r backend\requirements-ml.txt
Set-Location frontend
npm.cmd install
Set-Location ..
```

### Terminal 1: backend and local ML

```powershell
$env:PYTHONPATH = (Resolve-Path .\ml-engine).Path
$env:AEGIS_CORS_ORIGINS = '["http://localhost:5173","http://localhost:5175"]'
$env:AEGIS_DATABASE_PATH = Join-Path $env:TEMP 'aegis-adora-demo.sqlite3'
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Check API startup in Terminal 1 with `http://127.0.0.1:8000/health` and
`http://127.0.0.1:8000/docs`.

### Terminal 2: seed complete synthetic history

```powershell
backend\.venv\Scripts\python.exe data-engine\adapters\backend_ingest.py --readings 60 --scenario normal --seed 42
```

The adapter creates or reuses `AST-001`, stores heart rate, SpO2, respiration,
and the separate synthetic skin-temperature feature, and omits legacy
`body_temperature_c`. Run the same command again to verify idempotency: exact
existing readings are reused, never inserted again or replaced.

### Terminal 3: frontend

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
$env:VITE_API_TIMEOUT_MS = '10000'
$env:VITE_ASSISTANT_MODE = 'mock'
Set-Location frontend
npm.cmd run dev -- --host localhost --port 5175
```

Open `http://localhost:5175/`. It starts in **DEMO MODE**; choose **LIVE API
MODE** and select `AST-001` to view stored history. Select **RUN LOCAL ML
ANALYSIS** in LIVE API MODE to invoke the real backend ML engine. The result is
an algorithmic output on synthetic inputs, not a medical assessment. Generic
vital alerts remain global; only explicit synthetic region markers can
highlight a body region.

To request the same real local ML analysis directly from PowerShell instead of
the UI button, run this from the repository root while Terminal 1 is serving:

```powershell
$analysisBody = @{ mode = 'local'; source = 'synthetic_data_engine'; history_limit = 100; temperature_is_skin = $false } | ConvertTo-Json
$analysis = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/health/AST-001/analyses' -ContentType 'application/json' -Body $analysisBody
$analysis | ConvertTo-Json -Depth 20
```

For the dashboard's user-submitted assistant chat, native Gemini provider
configuration, and mock/offline behavior, see
[docs/gemini-dashboard-chat.md](docs/gemini-dashboard-chat.md).

Check `is_mock` is `false`, `model_version` is present, and `status` is the
actual algorithmic result (`normal`, `anomaly`, or `insufficient_data`). The
command does not infer a result from the Data Engine's scenario label.

### Verify scenarios, anatomy, and assistant label

- In DEMO MODE, inspect all ten scenarios. Heart-rate, SpO2, and respiration
  alerts are global. The separate left-arm warning and right-arm critical
  synthetic markers highlight only their named arms. The mixed scenario shows
  three global vital alerts and three explicit localized markers. Additional
  critical scenarios cover each limb and multiple localized critical markers.
- Select **FULL BODY**, **SKELETON**, **MUSCLES**, and **ORGANS**. Confirm the
  anatomical GLB appears. Drag to rotate, use the wheel to zoom, and select the
  reset control. Region selection changes navigation/highlighting only.
- Assistant mode is explicitly `mock`; the interface labels the mock response.
  These commands do not start an assistant service or claim real LLM output.

Stop Uvicorn and Vite with **Ctrl+C** in their terminals. The SQLite file stays
under `$env:TEMP`; the commands do not delete it automatically.

For a frontend-only run, the dashboard starts in Demo Mode and needs no API.
For API and data contracts, see [`docs/api-contracts.md`](docs/api-contracts.md)
and [`docs/data-schema.md`](docs/data-schema.md).

## Run the backend

For the project-safe backend startup command and `AEGIS_DATABASE_PATH` setup,
use Terminal 1 in the integrated demo instructions above. The default backend
path remains `backend/aegis.sqlite3` for existing users; do not omit the
temporary-path override when running the seeded demo.

## Data and safety

`data/synthetic/sample_reading.json` is a fabricated example to demonstrate the
shared format. It is not sourced from NASA or any person. Do not use prototype
outputs to make medical, operational, or mission decisions. Scientific
references and any future validation evidence must be reviewed and documented
before they are used to support claims.
