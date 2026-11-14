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

## Planned capabilities

- Ingest and validate clearly identified synthetic sensor readings.
- Prepare sensor data for downstream analysis and personalized baselines.
- Explore anomaly-detection models and communicate their outputs with context.
- Provide a safety-conscious health assistant that explains prototype outputs.
- Visualize status in an interactive astronaut digital twin.
- Keep each module independently developable through shared schemas and API
  contracts.

The ML, assistant, frontend, and digital-twin capabilities are **not implemented
yet**. This initial project provides the repository structure, documentation,
sample data, and a minimal health-check API.

## Technology stack

| Area | Foundation / planned technology |
|---|---|
| Backend API | Python, FastAPI, Uvicorn |
| Data and ML engines | Python; libraries will be selected as modules are developed |
| AI assistant | Separate assistant, explanation, knowledge, and safety modules |
| Frontend | Independent web application (framework to be selected by the team) |
| Digital twin | Independent visualization module and asset pipeline |
| Integration | JSON sensor contract and HTTP API |

## Six-member team responsibilities

These are role assignments, not named team members. Keep module ownership
separate and integrate through the documented JSON schema and API contracts.

| Member | Primary responsibility | Integration deliverable |
|---|---|---|
| 1 | Backend and API | FastAPI endpoints and stable response contracts |
| 2 | Data engine | Synthetic fixtures, validation, and preprocessing |
| 3 | ML engine | Baseline and anomaly-detection experiments with evaluation notes |
| 4 | AI assistant and safety | Explanations, bounded responses, and safety rules |
| 5 | Frontend | User workflows and API integration |
| 6 | Digital twin and integration | Twin visualization, shared contracts, and cross-module integration |

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

## Run the backend

From the repository root, create and activate a virtual environment, install the
backend dependencies, and start the development server.

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload
```

**Windows Command Prompt**

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r backend\requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://127.0.0.1:8000`. Check
`http://127.0.0.1:8000/health` for the JSON health response, or open
`http://127.0.0.1:8000/docs` for the automatically generated API documentation.
The first install requires an internet connection. If PowerShell blocks
activation, use the Command Prompt instructions or follow your organization's
virtual-environment policy.

## Data and safety

`data/synthetic/sample_reading.json` is a fabricated example to demonstrate the
shared format. It is not sourced from NASA or any person. Do not use prototype
outputs to make medical, operational, or mission decisions. Scientific
references and any future validation evidence must be reviewed and documented
before they are used to support claims.
