# AEGIS local API contracts

These are local prototype contracts for explicitly synthetic inputs. FastAPI
serves the authoritative detailed schemas at `/openapi.json` and `/docs`.
Requests reject unknown fields; timestamps must include a timezone. The API
does not provide medical decisions, validated alert limits, or NASA telemetry.

## `GET /health`

Indicates whether the API process is responding. This is a service health check;
it does not indicate astronaut or system health.

**Success — `200 OK`**

```json
{
  "status": "ok"
}
```

There are no request parameters or request body. This response only confirms API
availability; it does not indicate astronaut health.

## Synthetic data and profile

`POST /astronauts` creates a fictional profile. Mark synthetic profiles in
`profile_metadata`, for example:

```json
{
  "astronaut_id": "AST-001",
  "name": "Synthetic Demonstration Astronaut",
  "mission_id": "AEGIS-DEMO",
  "mission_role": "synthetic software demonstration",
  "profile_metadata": {"data_source": "synthetic_data_engine", "is_simulated": true}
}
```

`POST /health/ingest` accepts either one sensor row or one grouped record. The
data-engine adapter uses the grouped form and sends only supported fields:

```json
{
  "astronaut_id": "AST-001",
  "timestamp": "2026-01-01T00:00:00Z",
  "sensor_type": "synthetic_multi_sensor",
  "data_source": "synthetic_data_engine",
  "is_simulated": true,
  "quality": "synthetic_demo",
  "heart_rate": {"value": 72, "unit": "bpm"},
  "spo2": {"value": 98, "unit": "%"},
  "skin_temperature": {"value": 31.8, "unit": "degC"},
  "respiration_rate": {"value": 16, "unit": "breaths/min"}
}
```

Each stored row retains `astronaut_id`, UTC timestamp, `measurement_type`,
numeric `value`, exact `unit`, `sensor_type`, `source`, `is_simulated`, and
optional `quality`. New rows return HTTP `201`. An exact retry with the same
astronaut, timestamp, measurement, source, sensor type, unit, value, simulation
flag, and quality returns the existing row(s) with HTTP `200`; no duplicate is
inserted. Reusing an identity with different content returns HTTP `409` and
does not overwrite the saved row. Historical duplicates already in an older
database are preserved; startup skips the optional unique index when those
duplicates exist and ingestion reports an ambiguous identity as a conflict.

All readings used for demonstration and analysis must have `is_simulated: true`
and a source beginning with `synthetic`. The adapter omits the ambiguous legacy
`body_temperature_c` field and maps only the separately generated
`skin_temperature_c` value to `skin_temperature`; see
[`data-schema.md`](./data-schema.md).

The default database remains `backend/aegis.sqlite3`. To isolate a local demo
or test, set `AEGIS_DATABASE_PATH` to an absolute SQLite file path **before**
starting Uvicorn. For example, PowerShell may use
`$env:AEGIS_DATABASE_PATH = Join-Path $env:TEMP 'aegis-adora-demo.sqlite3'`.
The backend creates missing tables and never replaces or deletes the database.

## Readings, analysis, and assistant

| Method | Path | Purpose |
|---|---|---|
| GET | `/astronauts` | List profiles; the UI filters for synthetic profile metadata |
| GET | `/health/{astronaut_id}/latest` | Latest row per measurement type |
| GET | `/health/{astronaut_id}/history?measurement_type=heart_rate` | Chronological sensor history; supports time bounds and pagination |
| POST | `/health/{astronaut_id}/analyses` | Store an explicit `mock` or `local` ML analysis |
| GET | `/health/{astronaut_id}/analyses/latest` | Retrieve the most recent stored analysis (404 when absent) |
| POST | `/ai/assistant` | Request an explicitly labelled mock reply or configured local explanation |

Analysis request:

```json
{
  "mode": "local",
  "source": "synthetic_data_engine",
  "history_limit": 100,
  "temperature_is_skin": false
}
```

Use `mode: "local"` to invoke Member 2's engine. A missing runtime or invalid
provider result returns an error; it is never reported as successful mock or
real inference. Insufficient data remains explicitly unknown. The analysis
response carries `is_mock`, status, affected measurement names, model version,
preparation notes, and the full nested ML result. Scores are not medical
probabilities, and affected measurement names are not mapped to anatomy.
The local ML adapter reads the explicit `skin_temperature` measurement as its
`temperature` model input. A legacy measurement named `temperature` remains
excluded unless the caller explicitly sends `temperature_is_skin: true`; this
flag does not change or relabel stored data.
Relevant analysis fields include `status` (`mock`, `normal`, `anomaly`, or
`insufficient_data`), nullable `anomaly_detected` and `anomaly_score`,
`affected_measurements`, `is_mock`, `data_source`, and `ml_result`. A mock result
must remain labelled and keeps its anomaly fields unknown.

Assistant request:

```json
{
  "astronaut_id": "AST-001",
  "question": "Explain this synthetic analysis.",
  "mode": "local",
  "analysis_id": 1
}
```

The backend forwards only the selected analysis summary. Configure
`AEGIS_ASSISTANT_URL=http://127.0.0.1:8001` to connect Member 3's existing
`POST /api/v1/assistant/respond` contract. The assistant needs a local provider
to produce a non-mock explanation; otherwise the backend reports unavailability
and a caller may explicitly retry with `mode: "mock"`. Responses include
`answer`, `assistant_version`, `is_mock`, `limitations`, `status`, `data_source`,
and the selected minimal `context`.

FastAPI's interactive development documentation is available at `/docs` while
the local server is running.
