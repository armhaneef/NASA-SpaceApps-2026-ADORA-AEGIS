# Phase 3 backend API draft

This backend-local contract is implemented for development and awaits team
review. It does not change `docs/api-contracts.md` or `docs/data-schema.md`.
The agreed `GET /health` response remains `{"status":"ok"}`.

## Endpoints

| Method | Path | Success |
| --- | --- | --- |
| POST | `/astronauts` | 201, created profile |
| GET | `/astronauts` | 200, array ordered by astronaut ID |
| GET | `/astronauts/{astronaut_id}` | 200, profile |
| PATCH | `/astronauts/{astronaut_id}` | 200, updated profile |
| DELETE | `/astronauts/{astronaut_id}` | 204, empty body |
| POST | `/health/ingest` | 201, array of stored readings with database IDs |
| GET | `/health/{astronaut_id}/latest` | 200, array, newest per measurement type |
| GET | `/health/{astronaut_id}/history` | 200, chronological array |

Unknown astronaut: 404. Duplicate astronaut ID or deletion with stored readings:
409. Invalid body/query: 422 with `detail` (validation errors include location
and message). Internal database errors are not exposed to clients. An existing
astronaut with no readings returns `[]`, not 404. All responses are JSON except
204. Extra body fields are rejected to catch misspelled fields.

PATCH updates supplied fields only. IDs and creation times are immutable. Empty
patches and null profile fields are rejected. Metadata updates replace the whole
metadata object; they do not recursively merge it. There is no bulk delete or
cascading deletion of readings.

`GET /astronauts` and history accept `limit` (1–1000, default 100) and `offset`
(nonnegative, default 0). Arrays are deliberately simple; use pagination to
retrieve additional pages. Offset pagination is intended for this local MVP.

## Numeric ingestion

```json
{
  "astronaut_id": "AST-001",
  "timestamp": "2026-11-14T10:00:00Z",
  "sensor_type": "smart_band",
  "measurement_type": "heart_rate",
  "value": 78,
  "unit": "beats/min",
  "source": "synthetic_example",
  "is_simulated": true,
  "quality": "simulated"
}
```

`quality` is optional; all other fields shown are required. Simulation status
must be an explicit JSON boolean, not inferred from source or quality. For the
hackathon examples use fictional profiles and simulated readings. Sensor type
and source are nonempty descriptive labels, not claims of hardware connectivity.
Timestamps require timezone information and are returned in UTC. Future
timestamps are accepted because these are simulated mission scenarios.

Values must be finite JSON numbers; booleans and numeric strings are rejected.
The following draft registry defines accepted types, exact unit labels, and
numeric domains, not clinical thresholds. No alerts or analyses are generated.

| Type | Units | Numeric domain |
| --- | --- | --- |
| heart_rate | `beats/min`, `bpm` | nonnegative |
| spo2 | `%` | 0–100 |
| temperature, skin_temperature | `degC` | finite |
| respiration_rate | `breaths/min` | nonnegative |
| co2 | `ppm` | nonnegative |
| humidity | `%` | 0–100 |
| sleep_duration | `h`, `min` | nonnegative |
| activity_steps | `steps` | nonnegative |
| radiation_dose | `mSv`, `uSv` | nonnegative |

Units are preserved exactly after trimming whitespace. No conversion is
performed: a chart must not combine readings with different units without
explicit conversion. Registry extensions need team agreement and tests. ECG/EEG
waveforms, biochemical indicators, and unagreed summaries are not accepted.

## Compatibility with grouped records

The same endpoint also accepts shared grouped measurement fields, with explicit
provenance added rather than guessed:

```json
{
  "astronaut_id": "AST-001",
  "timestamp": "2026-11-14T10:00:00Z",
  "sensor_type": "synthetic_multi_sensor",
  "data_source": "synthetic_example",
  "is_simulated": true,
  "heart_rate": {"value": 78, "unit": "beats/min"},
  "spo2": {"value": 98, "unit": "%"}
}
```

Supported grouped fields are `heart_rate`, `spo2`, `temperature`,
`respiration_rate`, and `co2`. At least one must be present. Omit absent fields;
explicit null measurements are rejected. The group is fully validated before
saving; one invalid measurement means none are stored. Each measurement becomes
a separate row with the supplied shared timestamp, sensor type, simulation flag,
quality, and `data_source` mapped to `source`. Use individual requests when
measurements have different sources or timestamps. Do not assign a physical
sensor label to measurements it cannot produce.

The existing shared fixture alone lacks required sensor and simulation metadata
and receives 422. Member 1 must supply those explicitly. The original single
reading proposal's `quality: "simulated"` also does not replace `is_simulated`.
Arbitrary arrays/batch requests are not implemented. Repeated successful POSTs
create additional records; ingestion is not idempotent.

## Retrieval semantics

Both reading GET endpoints accept `measurement_type`; unknown types return 422.
Latest selects by measurement timestamp, not insertion time. Timestamp ties use
the greatest database ID. There is one result per type, ordered by type name,
even when different sensors or units contributed; each row retains provenance
and its own timestamp. Latest does not imply that the data is recent enough for
any particular application.

History accepts inclusive `start` and `end` ISO timestamps with timezone
information. Reversed bounds or timestamps without a timezone return 422.
History is ordered oldest first, then ascending ID for ties. Example:

```text
/health/AST-001/history?measurement_type=heart_rate&start=2026-11-14T00:00:00Z&end=2026-11-15T00:00:00Z&limit=100&offset=0
```

Keep the server bound to localhost for this phase. Authentication and frontend
CORS configuration are not implemented yet. Member 1 should review the input
mapping/registry and Members 5 and 6 should review retrieval and pagination
before cross-module integration. ML and assistant interfaces remain later work.
